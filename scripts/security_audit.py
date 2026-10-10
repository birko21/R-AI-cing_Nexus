from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = (
    ("PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----")),
    ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GITHUB_TOKEN", re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("STRIPE_LIVE_KEY", re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b")),
    ("PASSWORD_ASSIGNMENT", re.compile(r"(?i)\bpassword\s*[:=]\s*[\"'][^\"']{8,}[\"']")),
)
FRONTEND_SECRET_PATTERN = re.compile(r"import\.meta\.env\.(?:VITE|NEXT_PUBLIC)_[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)")


def scan_secrets(files: dict[str, str]) -> list[dict[str, str]]:
    return [{"path": path, "rule": rule} for path, text in files.items() for rule, pattern in SECRET_PATTERNS if pattern.search(text)]


def scan_frontend_secret_refs(files: dict[str, str]) -> list[str]:
    return sorted(path for path, text in files.items() if path.startswith("apps/web/") and FRONTEND_SECRET_PATTERN.search(text))


def tracked_source_files(root: Path) -> dict[str, str]:
    paths = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
    suffixes = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".toml", ".env", ".md", ".txt"}
    return {relative.replace("\\", "/"): (root / relative).read_text(encoding="utf-8") for relative in paths if (root / relative).is_file() and (root / relative).suffix in suffixes}


def build_report(root: Path) -> dict[str, object]:
    files = tracked_source_files(root)
    secret_findings = scan_secrets(files)
    frontend_findings = scan_frontend_secret_refs(files)
    return {
        "schema_version": "security-audit-v1", "scanned_files": len(files), "secret_findings": secret_findings,
        "frontend_secret_refs": frontend_findings,
        "lockfiles": {path: (root / path).is_file() for path in ("pnpm-lock.yaml", "services/api/requirements.lock.txt")},
        "log_redaction_control": "app.egress.redact_text", "provider_keys": "SERVER_SIDE_ONLY",
        "status": "PASS" if not secret_findings and not frontend_findings else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "evidence" / "ril-057" / "security-audit.json")
    args = parser.parse_args()
    report = build_report(ROOT)
    if args.write_report:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"SECURITY AUDIT {report['status']}: files={report['scanned_files']} secret_findings={len(report['secret_findings'])} frontend_secret_refs={len(report['frontend_secret_refs'])}")
    if report["status"] != "PASS" or not all(report["lockfiles"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
