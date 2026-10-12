"""Project validated synthetic envelopes into the canonical PostgreSQL tables."""

from __future__ import annotations

import json

from sqlalchemy import Connection, text

from app.betfair_mock import SyntheticBetfairMarket
from app.forecast_archive import ForecastManifest
from app.provenance import RawEnvelope


def project_synthetic_market(connection: Connection, market: SyntheticBetfairMarket, envelope: RawEnvelope) -> dict[str, str]:
    """Append one validated market fixture to canonical identity projections."""

    receipt_id = f"receipt:{envelope.envelope_id}"
    meeting_id = f"synthetic-meeting:{market.code.lower()}"
    connection.execute(
        text(
            """
            INSERT INTO source_receipts (
                source_receipt_id, source_identifier, payload_sha256, schema_version,
                first_observed_at, published_at, rights_state, data_mode
            ) VALUES (
                :source_receipt_id, :source_identifier, :payload_sha256, :schema_version,
                :first_observed_at, :published_at, :rights_state, :data_mode
            ) ON CONFLICT (source_receipt_id) DO NOTHING
            """
        ),
        {
            "source_receipt_id": receipt_id,
            "source_identifier": envelope.source_identifier,
            "payload_sha256": envelope.payload_sha256,
            "schema_version": envelope.schema_version,
            "first_observed_at": envelope.first_observed_at,
            "published_at": envelope.published_at,
            "rights_state": envelope.rights_state,
            "data_mode": envelope.data_mode,
        },
    )
    connection.execute(
        text(
            """
            INSERT INTO meetings (
                meeting_id, code, name, country, scheduled_at, data_mode,
                source_receipt_id, first_observed_at
            ) VALUES (
                :meeting_id, :code, :name, 'AUS', :scheduled_at, :data_mode,
                :source_receipt_id, :first_observed_at
            ) ON CONFLICT (meeting_id) DO NOTHING
            """
        ),
        {
            "meeting_id": meeting_id,
            "code": market.code,
            "name": market.venue,
            "scheduled_at": market.market_start_time,
            "data_mode": envelope.data_mode,
            "source_receipt_id": receipt_id,
            "first_observed_at": envelope.first_observed_at,
        },
    )
    connection.execute(
        text(
            """
            INSERT INTO race_revisions (
                race_id, meeting_id, race_number, status, field_revision,
                effective_from, first_observed_at, data_mode, source_receipt_id
            ) VALUES (
                :race_id, :meeting_id, :race_number, 'FINAL_FIELDS', :field_revision,
                :effective_from, :first_observed_at, :data_mode, :source_receipt_id
            ) ON CONFLICT (race_id, field_revision) DO NOTHING
            """
        ),
        {
            "race_id": market.race_id,
            "meeting_id": meeting_id,
            "race_number": int(market.race_id.rsplit(":", 1)[-1]),
            "field_revision": market.field_revision,
            "effective_from": market.market_start_time,
            "first_observed_at": envelope.first_observed_at,
            "data_mode": envelope.data_mode,
            "source_receipt_id": receipt_id,
        },
    )
    race_revision_id = connection.execute(
        text("SELECT race_revision_id FROM race_revisions WHERE race_id = :race_id AND field_revision = :field_revision"),
        {"race_id": market.race_id, "field_revision": market.field_revision},
    ).scalar_one()
    for number, runner in enumerate(market.runners, start=1):
        connection.execute(
            text(
                """
                INSERT INTO participants (
                    participant_id, code, name, source_receipt_id, first_observed_at, data_mode
                ) VALUES (
                    :participant_id, :code, :name, :source_receipt_id, :first_observed_at, :data_mode
                ) ON CONFLICT (participant_id) DO NOTHING
                """
            ),
            {
                "participant_id": runner.entry_id,
                "code": market.code,
                "name": runner.runner_name,
                "source_receipt_id": receipt_id,
                "first_observed_at": envelope.first_observed_at,
                "data_mode": envelope.data_mode,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO entry_revisions (
                    entry_id, race_revision_id, participant_id, number, status,
                    effective_from, first_observed_at, data_mode, source_receipt_id
                )
                SELECT :entry_id, :race_revision_id, :participant_id, :number, :status,
                       :effective_from, :first_observed_at, :data_mode, :source_receipt_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM entry_revisions
                    WHERE entry_id = :entry_id AND race_revision_id = :race_revision_id
                )
                """
            ),
            {
                "entry_id": runner.entry_id,
                "race_revision_id": race_revision_id,
                "participant_id": runner.entry_id,
                "number": number,
                "status": "ACTIVE" if runner.status == "ACTIVE" else "SCRATCHED",
                "effective_from": market.market_start_time,
                "first_observed_at": envelope.first_observed_at,
                "data_mode": envelope.data_mode,
                "source_receipt_id": receipt_id,
            },
        )
    return {"receipt_id": receipt_id, "meeting_id": meeting_id, "race_id": market.race_id}


def append_forecast_manifest(connection: Connection, manifest: ForecastManifest) -> None:
    """Append a verified immutable forecast manifest to PostgreSQL."""

    from app.forecast_archive import verify_manifest

    payload = manifest.to_dict()
    verify_manifest(payload)
    output = payload["output"]
    probabilities = {
        runner["entry_id"]: runner["probability"]
        for runner in output["runners"]
        if runner["probability"] is not None
    }
    connection.execute(
        text(
            """
            INSERT INTO forecast_archives (
                forecast_id, race_id, field_revision, cutoff_at, model_version,
                manifest_sha256, probabilities, data_mode
            ) VALUES (
                :forecast_id, :race_id, :field_revision, :cutoff_at, :model_version,
                :manifest_sha256, CAST(:probabilities AS jsonb), :data_mode
            ) ON CONFLICT (forecast_id) DO NOTHING
            """
        ),
        {
            "forecast_id": manifest.forecast_id,
            "race_id": manifest.race_id,
            "field_revision": manifest.field_revision,
            "cutoff_at": manifest.cutoff,
            "model_version": output["model_version"],
            "manifest_sha256": manifest.manifest_hash,
            "probabilities": json.dumps(probabilities, sort_keys=True),
            "data_mode": manifest.data_mode,
        },
    )
