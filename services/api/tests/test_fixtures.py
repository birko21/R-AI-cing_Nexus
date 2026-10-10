import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[3]
FIXTURE = ROOT / "fixtures" / "synthetic" / "fixture.json"
MANIFEST = ROOT / "fixtures" / "synthetic" / "manifest.json"


def test_committed_fixture_is_watermarked_and_covers_all_required_collections() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert fixture["data_mode"] == "SYNTHETIC_ONLY"
    assert fixture["fictional"] is True
    assert fixture["watermark"] == "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE"
    assert set(fixture["codes"]) == {"THOROUGHBRED", "HARNESS", "GREYHOUND"}
    required = {"meetings", "races", "entries", "historical_runs", "sections", "scratchings", "reserves", "quotes", "results", "corrections", "edge_cases"}
    assert required.issubset(fixture["collections"])
    assert all(item["watermark"] == fixture["watermark"] for values in fixture["collections"].values() for item in values)
    assert manifest["files"]["fixture.json"]["sha256"]


def test_seed_replay_produces_identical_fixture(tmp_path: Path) -> None:
    output = tmp_path / "fixture.json"
    manifest = tmp_path / "manifest.json"
    command = [sys.executable, "scripts/generate_synthetic_fixtures.py", "--output", str(output), "--manifest", str(manifest), "--seed", "test-seed"]
    first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    first_bytes = output.read_bytes()
    second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert first.returncode == 0
    assert second.returncode == 0
    assert first_bytes == output.read_bytes()
