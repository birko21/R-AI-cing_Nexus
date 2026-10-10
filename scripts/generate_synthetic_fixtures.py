from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


WATERMARK = "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE"
DATA_MODE = "SYNTHETIC_ONLY"
DEMO_DATE = "2026-01-15"
CODES = (
    ("THOROUGHBRED", "Fictional Thoroughbred Park"),
    ("HARNESS", "Fictional Harness Circuit"),
    ("GREYHOUND", "Fictional Greyhound Track"),
)


def canonical(code: str, kind: str, source_id: str) -> str:
    return f"{code}:synthetic:{kind}-{source_id}"


def record(record_id: str, **fields: object) -> dict[str, object]:
    return {
        "record_id": record_id,
        "fictional": True,
        "data_mode": DATA_MODE,
        "watermark": WATERMARK,
        **fields,
    }


def build_fixture(seed: str) -> dict[str, object]:
    collections: dict[str, list[dict[str, object]]] = {
        "codes": [],
        "meetings": [],
        "races": [],
        "entries": [],
        "historical_runs": [],
        "sections": [],
        "scratchings": [],
        "reserves": [],
        "quotes": [],
        "results": [],
        "corrections": [],
        "edge_cases": [],
    }

    for code, label in CODES:
        collections["codes"].append(record(code, code=code, label=label))
        meeting_id = canonical(code, "meeting", "001")
        collections["meetings"].append(
            record(
                meeting_id,
                meeting_id=meeting_id,
                code=code,
                name=label,
                country="AUS",
                scheduled_at=f"{DEMO_DATE}T03:00:00Z",
                demo_date=DEMO_DATE,
            )
        )

        for race_number in (1, 2):
            race_id = canonical(code, "race", f"001-{race_number:02d}")
            revision = f"{race_id}:field-r1"
            status = "OFFICIAL" if race_number == 1 else "FINAL_FIELDS"
            collections["races"].append(
                record(
                    race_id,
                    race_id=race_id,
                    meeting_id=meeting_id,
                    code=code,
                    race_number=race_number,
                    status=status,
                    field_revision=revision,
                    scheduled_at=f"{DEMO_DATE}T{3 + race_number:02d}:00:00Z",
                )
            )
            for number in range(1, 5):
                participant_id = canonical(code, "participant", f"{race_number:02d}-{number:02d}")
                entry_id = canonical(code, "entry", f"001-{race_number:02d}-{number:02d}")
                collections["entries"].append(
                    record(
                        entry_id,
                        entry_id=entry_id,
                        race_id=race_id,
                        participant_id=participant_id,
                        code=code,
                        number=number,
                        name=f"Fictional {code.title()} Runner {race_number}-{number}",
                        status="ACTIVE" if number != 4 or race_number == 1 else "COUPLED",
                        field_revision=revision,
                    )
                )
                for run_number in range(1, 4):
                    collections["historical_runs"].append(
                        record(
                            f"{entry_id}:run-{run_number}",
                            participant_id=participant_id,
                            code=code,
                            run_date=f"2025-12-{10 + run_number:02d}",
                            distance=1000 + (run_number * 200),
                            finish_position=((number + run_number) % 4) + 1,
                            source_receipt_id=f"synthetic://{code.lower()}/run-{run_number}",
                        )
                    )
            collections["sections"].append(
                record(
                    f"{race_id}:section-1",
                    race_id=race_id,
                    code=code,
                    section_type="FINAL_SPLIT" if code != "GREYHOUND" else "FIRST_SPLIT",
                    values=[12.1 + race_number, 12.4 + race_number, 12.8 + race_number],
                )
            )
            collections["quotes"].append(
                record(
                    f"{race_id}:quote-demo",
                    race_id=race_id,
                    code=code,
                    quote_type="SYNTHETIC_INDICATIVE",
                    captured_at=f"{DEMO_DATE}T{2 + race_number:02d}:30:00Z",
                    values={str(number): round(2.0 + (number * 0.7) + (race_number * 0.1), 2) for number in range(1, 5)},
                )
            )

        race_one = canonical(code, "race", "001-01")
        collections["results"].append(
            record(
                f"{race_one}:result-r1",
                race_id=race_one,
                code=code,
                result_status="OFFICIAL",
                winner_entry_id=canonical(code, "entry", "001-01-01"),
                resolved_at=f"{DEMO_DATE}T06:00:00Z",
            )
        )
        collections["corrections"].append(
            record(
                f"{race_one}:correction-r2",
                race_id=race_one,
                code=code,
                correction_type="RESULT_ADDENDUM",
                prior_result_record=f"{race_one}:result-r1",
                correction_note="Fictional correction for replay testing; prior result remains immutable.",
                corrected_at=f"{DEMO_DATE}T07:00:00Z",
            )
        )
        race_two = canonical(code, "race", "001-02")
        scratched_entry = canonical(code, "entry", "001-02-02")
        reserve_entry = canonical(code, "entry", "001-02-04")
        collections["scratchings"].append(
            record(
                f"{scratched_entry}:scratching-1",
                race_id=race_two,
                entry_id=scratched_entry,
                code=code,
                reason="FICTIONAL_LATE_SCRATCHING",
                observed_at=f"{DEMO_DATE}T04:00:00Z",
            )
        )
        collections["reserves"].append(
            record(
                f"{reserve_entry}:reserve-1",
                race_id=race_two,
                entry_id=reserve_entry,
                code=code,
                reserve_order=1,
                activated=False,
            )
        )
        collections["edge_cases"].extend(
            [
                record(f"{code}:edge-coupled", code=code, case="COUPLED_ENTRY", expected_behavior="ABSTAIN"),
                record(f"{code}:edge-incomplete", code=code, case="INCOMPLETE_FIELD", expected_behavior="ABSTAIN"),
                record(f"{code}:edge-no-racing", code=code, case="NO_RACING", expected_behavior="NOT_AVAILABLE"),
                record(f"{code}:edge-dead-heat", code=code, case="DEAD_HEAT", expected_behavior="EXCLUDE_PRIMARY_SCORING"),
            ]
        )

    return {
        "fixture_id": "ril-016-three-code-v1",
        "seed": seed,
        "demo_date": DEMO_DATE,
        "fictional": True,
        "data_mode": DATA_MODE,
        "watermark": WATERMARK,
        "codes": [code for code, _ in CODES],
        "collections": collections,
    }


def write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fixture_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_fixture(output: Path, manifest_path: Path, seed: str) -> None:
    fixture = build_fixture(seed)
    write_json(output, fixture)
    manifest = {
        "fixture_id": fixture["fixture_id"],
        "seed": seed,
        "demo_date": DEMO_DATE,
        "fictional": True,
        "data_mode": DATA_MODE,
        "watermark": WATERMARK,
        "codes": list(fixture["codes"]),
        "files": {"fixture.json": {"sha256": fixture_hash(output), "path": str(output).replace("\\", "/")}},
        "record_counts": {name: len(items) for name, items in fixture["collections"].items()},
    }
    write_json(manifest_path, manifest)


def verify_fixture(output: Path, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = build_fixture(str(manifest["seed"]))
    actual = json.loads(output.read_text(encoding="utf-8"))
    if actual != expected:
        raise SystemExit("SYNTHETIC FIXTURE CHECK FAILED: seed replay differs")
    if manifest["data_mode"] != DATA_MODE or manifest["fictional"] is not True or manifest["watermark"] != WATERMARK:
        raise SystemExit("SYNTHETIC FIXTURE CHECK FAILED: watermark or data mode missing")
    if manifest["files"]["fixture.json"]["sha256"] != fixture_hash(output):
        raise SystemExit("SYNTHETIC FIXTURE CHECK FAILED: fixture hash differs")
    print(f"SYNTHETIC FIXTURE VALID: {manifest['fixture_id']} / records={sum(manifest['record_counts'].values())}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("fixtures/synthetic/fixture.json"))
    parser.add_argument("--manifest", type=Path, default=Path("fixtures/synthetic/manifest.json"))
    parser.add_argument("--seed", default="RIL-016-seed-v1")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        verify_fixture(args.output, args.manifest)
    else:
        write_fixture(args.output, args.manifest, args.seed)
        verify_fixture(args.output, args.manifest)


if __name__ == "__main__":
    main()
