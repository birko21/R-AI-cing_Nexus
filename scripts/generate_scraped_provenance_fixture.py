from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.provenance import RawEnvelope, payload_sha256  # noqa: E402
from app.scraped_provenance import ReplayFixture, ScrapedProvenanceStore, ScrapedSourceReceipt  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "scraped_provenance_v1.json"
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)
PAYLOAD = {"race": "PUBLIC:fixture:race-1", "status": "OFFICIAL"}


def build_fixture() -> dict[str, object]:
    replay_fixture = ReplayFixture.from_payload("replay-1", PAYLOAD, "parser-v1")
    envelope = RawEnvelope(
        envelope_id="env-1", source_identifier="https://public.example/racing/race-1", payload=PAYLOAD,
        payload_sha256=payload_sha256(PAYLOAD), schema_version="scraped-race-v1", retrieved_at=NOW,
        first_observed_at=NOW, data_mode="SCRAPED_PUBLIC", rights_state="UNASSESSED",
        retrieval_metadata={"parser_version": "parser-v1", "fixture_id": "replay-1"},
    )
    receipt = ScrapedSourceReceipt(
        receipt_id="receipt-1", envelope=envelope, retrieval_url="https://public.example/racing/race-1",
        retrieved_at=NOW, content_sha256=replay_fixture.content_sha256, parser_version="parser-v1",
        replay_fixture_id="replay-1", retention_until=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )
    store = ScrapedProvenanceStore()
    store.append(receipt, replay_fixture)
    return {
        "schema_version": "scraped-provenance-v1",
        "receipt": {
            **store.provenance_view("receipt-1", NOW), "envelope_id": envelope.envelope_id,
            "source_identifier": envelope.source_identifier, "envelope_payload_sha256": envelope.payload_sha256,
        },
        "replay_fixture": replay_fixture.to_dict(),
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Offline replay evidence only; no real public source was retrieved.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("SCRAPED PROVENANCE FIXTURE CHECK FAILED: generated content differs")
    print(f"SCRAPED PROVENANCE FIXTURE VALID: mode={expected['receipt']['data_mode']} retention={expected['receipt']['retention_status']}")


if __name__ == "__main__":
    main()
