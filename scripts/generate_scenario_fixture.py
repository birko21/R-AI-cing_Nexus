from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.scenario_studio import ScenarioRequest, run_scenario  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "scenario_studio_v1.json"


def build_fixture() -> dict[str, object]:
    request = ScenarioRequest(
        scenario_id="scenario-1", seed=42, sample_size=25, assumptions=("Synthetic field is complete",),
        observed_fact_ids=("receipt-1",), hypotheses=("Experimental pace scenario",), inputs={"pace": 0.6},
        model_version="scenario-v1", calibration_status="CALIBRATED", data_mode="SYNTHETIC_ONLY",
    )
    abstaining = request.model_copy(update={"scenario_id": "scenario-uncalibrated", "calibration_status": "ABSENT"})
    simulated = run_scenario(request)
    abstain = run_scenario(abstaining)
    return {
        "schema_version": "scenario-studio-v1", "simulated": simulated.model_dump(mode="json"), "abstain": abstain.model_dump(mode="json"),
        "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Seed replay and abstention evidence only; outputs are not calibrated predictions or wagering advice.",
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
        raise SystemExit("SCENARIO FIXTURE CHECK FAILED: generated content differs")
    print(f"SCENARIO FIXTURE VALID: simulated={expected['simulated']['status']} abstain={expected['abstain']['status']} hash={expected['simulated']['output_hash'][:12]}")


if __name__ == "__main__":
    main()
