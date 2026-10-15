"""Run one explicitly approved, read-only provider capture.

The command is intentionally operator-driven.  It never runs as part of API
startup, never places an order, and never prints credential material.  Without
``--persist`` the provider response is discarded after a shape/checksum
summary.  Persistence requires the adapter's historical/model approval gate.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import date
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.external_provider_integrations import ProviderActivationError  # noqa: E402
from app.live_provider_runtime import (  # noqa: E402
    build_live_provider_handle,
    configured_provider_status,
)
from app.provider_diagnostics import BoundedDiagnosticSession, DiagnosticPolicy  # noqa: E402
from app.live_ingestion import persist_approved_live_envelope  # noqa: E402
from app.betfair_live_projection import project_betfair_catalogue  # noqa: E402


DEFAULT_OPERATION = {
    "formfav": "LIST_MEETINGS",
    "punters-edge": "GET_RESULTS",
    "krok-odds": "LIST_MEETINGS",
    "betfair-exchange": "GET_MARKETS",
}


def _field_names(value: object, *, depth: int = 0) -> set[str]:
    if depth > 4:
        return set()
    if isinstance(value, list):
        fields: set[str] = set()
        for item in value[:100]:
            fields.update(_field_names(item, depth=depth + 1))
        return fields
    if not isinstance(value, Mapping):
        return set()
    fields: set[str] = set()
    for key, nested in value.items():
        if isinstance(key, str):
            fields.add(key)
        fields.update(_field_names(nested, depth=depth + 1))
    return fields


def _row_count(value: object, *, depth: int = 0) -> int:
    if depth > 4:
        return 0
    if isinstance(value, list):
        return len(value) + sum(_row_count(item, depth=depth + 1) for item in value[:100])
    if isinstance(value, Mapping):
        return sum(_row_count(item, depth=depth + 1) for item in value.values())
    return 0


def _contains_sensitive_key(value: object, *, depth: int = 0) -> bool:
    if depth > 5:
        return False
    sensitive = {"api_key", "app_key", "session_token", "token", "secret", "password", "authorization"}
    if isinstance(value, list):
        return any(_contains_sensitive_key(item, depth=depth + 1) for item in value[:100])
    if not isinstance(value, Mapping):
        return False
    return any(isinstance(key, str) and key.lower() in sensitive for key in value) or any(
        _contains_sensitive_key(item, depth=depth + 1) for item in value.values()
    )


def _summary(envelope) -> dict[str, object]:
    return {
        "envelope_id": envelope.envelope_id,
        "source_identifier": envelope.source_identifier,
        "payload_sha256": envelope.payload_sha256,
        "schema_version": envelope.schema_version,
        "retrieved_at": envelope.retrieved_at.isoformat(),
        "published_at": envelope.published_at.isoformat() if envelope.published_at else None,
        "data_mode": envelope.data_mode,
        "rights_state": envelope.rights_state,
        "payload_row_count": _row_count(envelope.payload),
        "payload_field_presence": sorted(_field_names(envelope.payload)),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one approved, read-only Nexus provider capture")
    parser.add_argument("--provider", choices=sorted(DEFAULT_OPERATION), help="provider ID; omit with --status")
    parser.add_argument("--operation", help="operation declared by the provider")
    parser.add_argument("--code", default="THOROUGHBRED", choices=["THOROUGHBRED"], help="audited racing code")
    parser.add_argument("--date", help="bounded YYYY-MM-DD date filter")
    parser.add_argument("--venue")
    parser.add_argument("--race", type=int)
    parser.add_argument("--view", choices=["catalogue", "book"], default="catalogue")
    parser.add_argument("--market-id", action="append", dest="market_ids", help="Betfair market ID; repeat for listMarketBook")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--persist", action="store_true", help="retain the approved raw envelope under data/live/raw")
    parser.add_argument("--persist-postgres", action="store_true", help="persist the approved raw envelope and source receipt to DATABASE_URL")
    parser.add_argument("--project-betfair", action="store_true", help="project an approved Betfair catalogue into canonical PostgreSQL race/entry tables")
    parser.add_argument("--diagnostic", action="store_true", help="run aggregate-only diagnostics; no raw payload is retained")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "live" / "raw")
    parser.add_argument("--status", action="store_true", help="show non-secret provider configuration status and exit")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.status:
        print(json.dumps(configured_provider_status(), indent=2, sort_keys=True))
        return 0
    if not args.provider:
        raise SystemExit("--provider is required unless --status is used")
    operation = args.operation or DEFAULT_OPERATION[args.provider]
    if args.date:
        try:
            date.fromisoformat(args.date)
        except ValueError as exc:
            raise SystemExit("--date must be YYYY-MM-DD") from exc
    if args.view == "book" and args.provider != "betfair-exchange":
        raise SystemExit("--view book is only valid for betfair-exchange")
    if args.view == "book" and not args.market_ids:
        raise SystemExit("Betfair listMarketBook requires at least one --market-id from a prior catalogue capture")
    if args.persist and args.persist_postgres:
        raise SystemExit("choose either --persist or --persist-postgres")
    if args.project_betfair and (args.provider != "betfair-exchange" or args.view != "catalogue" or not args.persist_postgres):
        raise SystemExit("--project-betfair requires betfair-exchange catalogue mode with --persist-postgres")
    if args.page_size < 1 or args.page_size > 100:
        raise SystemExit("--page-size must be between 1 and 100")

    handle = None
    try:
        handle = build_live_provider_handle(args.provider)
        if args.diagnostic:
            if args.persist or args.persist_postgres:
                raise ProviderActivationError("diagnostic mode cannot persist raw provider data")
            if not handle.config.diagnostics_enabled:
                raise ProviderActivationError("diagnostics are disabled; set NEXUS_DIAGNOSTICS_ENABLED=true explicitly")
            if args.provider != "punters-edge":
                raise ProviderActivationError("the bounded diagnostic workflow currently requires PuntersEdge account metadata")
            session = BoundedDiagnosticSession(
                handle.adapter,
                approval=handle.config.diagnostic_approvals,
                code=args.code,
                policy=DiagnosticPolicy(enabled=True),
            )
            metadata = session.run("ACCOUNT_METADATA_READ")
            result: dict[str, object] = {
                "status": "LIVE_DIAGNOSTIC_SUCCESS",
                "provider": args.provider,
                "metadata": metadata.model_dump(mode="json"),
            }
            if operation != "ACCOUNT_METADATA_READ":
                result["operation"] = session.run(
                    operation,
                    date=args.date,
                    venue=args.venue,
                    race=args.race,
                    view=args.view,
                ).model_dump(mode="json")
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        approval = handle.config.approval
        if approval is None:
            raise ProviderActivationError("a provider approval record is required; configure APPROVAL_FILE or approval environment fields")
        page = handle.adapter.fetch(
            operation,
            code=args.code,
            approval=approval,
            date=args.date,
            venue=args.venue,
            race=args.race,
            view=args.view,
            page_size=args.page_size,
            market_ids=tuple(args.market_ids or ()),
        )
        if len(page.records) != 1:
            raise ProviderActivationError("provider capture returned an unexpected envelope count")
        envelope = page.records[0]
        result: dict[str, object] = {
            "status": "LIVE_CAPTURE_SUCCESS",
            "provider": args.provider,
            "operation": operation,
            "persisted": False,
            "summary": _summary(envelope),
        }
        if args.persist_postgres:
            database_url = os.environ.get("DATABASE_URL", "").strip()
            if not database_url:
                raise ProviderActivationError("DATABASE_URL is required for --persist-postgres")
            if _contains_sensitive_key(envelope.payload):
                raise ProviderActivationError("provider payload contains a sensitive field name; PostgreSQL persistence stopped")
            from sqlalchemy import create_engine

            engine = create_engine(database_url, pool_pre_ping=True)
            try:
                with engine.begin() as connection:
                    result["postgres"] = persist_approved_live_envelope(connection, envelope)
                    result["projected"] = project_betfair_catalogue(connection, envelope) if args.project_betfair else None
            finally:
                engine.dispose()
            result["persisted"] = True
        if args.persist:
            if _contains_sensitive_key(envelope.payload):
                raise ProviderActivationError("provider payload contains a sensitive field name; raw persistence stopped")
            args.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = args.output_dir / f"{args.provider}-{operation.lower()}-{envelope.envelope_id}.json"
            output_path.write_text(envelope.model_dump_json(indent=2), encoding="utf-8")
            result["persisted"] = True
            result["output"] = str(output_path)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ProviderActivationError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "LIVE_CAPTURE_BLOCKED", "reason": str(exc)}, indent=2, sort_keys=True))
        return 2
    finally:
        if handle is not None:
            handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
