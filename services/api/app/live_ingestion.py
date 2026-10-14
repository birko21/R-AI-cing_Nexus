"""Persistence boundary for an approved live provider envelope.

Only a validated ``LICENSED``/``APPROVED`` envelope may cross this boundary.
The function writes the immutable source receipt and raw envelope in the
caller's transaction. It deliberately does not project provider-specific JSON
into canonical races; that requires a provider parser and identity report.
"""

from __future__ import annotations

from typing import TypedDict

from sqlalchemy import Connection, text

from app.ingestion import PostgresIngestionStore, RecordDisposition
from app.provenance import RawEnvelope


class LivePersistenceResult(TypedDict):
    source_receipt_id: str
    envelope_id: str
    disposition: RecordDisposition


def persist_approved_live_envelope(connection: Connection, envelope: RawEnvelope) -> LivePersistenceResult:
    if envelope.data_mode != "LICENSED" or envelope.rights_state != "APPROVED":
        raise ValueError("only licensed, approved live envelopes may be persisted")
    source_receipt_id = f"receipt:{envelope.envelope_id}"
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
            "source_receipt_id": source_receipt_id,
            "source_identifier": envelope.source_identifier,
            "payload_sha256": envelope.payload_sha256,
            "schema_version": envelope.schema_version,
            "first_observed_at": envelope.first_observed_at,
            "published_at": envelope.published_at,
            "rights_state": envelope.rights_state,
            "data_mode": envelope.data_mode,
        },
    )
    disposition = PostgresIngestionStore(connection).append_envelope(envelope)
    return {
        "source_receipt_id": source_receipt_id,
        "envelope_id": envelope.envelope_id,
        "disposition": disposition,
    }
