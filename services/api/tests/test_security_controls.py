from pathlib import Path

from app.egress import redact_text

ROOT = Path(__file__).resolve().parents[3]


def test_lockfiles_are_present_and_frontend_has_no_provider_secret_pattern() -> None:
    assert (ROOT / "pnpm-lock.yaml").is_file()
    assert (ROOT / "services/api/requirements.lock.txt").is_file()
    frontend = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "apps/web/src").glob("*.tsx"))
    assert "import.meta.env.VITE_API_KEY" not in frontend
    assert "import.meta.env.VITE_SECRET" not in frontend


def test_log_redaction_removes_sensitive_values() -> None:
    result = redact_text("Authorization: Bearer abc.secret.token email owner@example.com")
    assert "abc.secret.token" not in result.text
    assert "owner@example.com" not in result.text
