from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app import auth


@pytest.fixture
def oidc_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def make_token(key: rsa.RSAPrivateKey, *, scopes: str = "races:read") -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "iss": "https://issuer.example.test",
            "aud": "nexus-staging",
            "sub": "owner-123",
            "scope": scopes,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def configure_oidc(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("AUTH_MODE", "oidc")
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example.test")
    monkeypatch.setenv("OIDC_AUDIENCE", "nexus-staging")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://issuer.example.test/.well-known/jwks.json")
    monkeypatch.setenv("ALLOW_LOCAL_AUTH", "false")


def test_oidc_validates_signature_issuer_audience_and_scope(monkeypatch: pytest.MonkeyPatch, oidc_key: rsa.RSAPrivateKey) -> None:
    configure_oidc(monkeypatch)
    public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(oidc_key.public_key()))
    public_jwk["kid"] = "test-key"
    monkeypatch.setattr(auth, "_jwks", lambda force_refresh=False: (public_jwk,))

    identity = auth.races_read("Bearer " + make_token(oidc_key))

    assert identity["subject"] == "owner-123"
    assert identity["scopes"] == ["races:read"]


def test_oidc_rejects_bad_signature_and_missing_scope(monkeypatch: pytest.MonkeyPatch, oidc_key: rsa.RSAPrivateKey) -> None:
    configure_oidc(monkeypatch)
    public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(oidc_key.public_key()))
    public_jwk["kid"] = "test-key"
    monkeypatch.setattr(auth, "_jwks", lambda force_refresh=False: (public_jwk,))
    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(HTTPException) as invalid:
        auth.races_read("Bearer " + make_token(wrong_key))
    assert invalid.value.status_code == 401

    with pytest.raises(HTTPException) as forbidden:
        auth.races_read("Bearer " + make_token(oidc_key, scopes="forecasts:read"))
    assert forbidden.value.status_code == 403


def test_external_bind_requires_complete_https_oidc_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("AUTH_MODE", "oidc")
    monkeypatch.setenv("OIDC_ISSUER", "http://issuer.example.test")
    monkeypatch.setenv("OIDC_AUDIENCE", "nexus-staging")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://issuer.example.test/.well-known/jwks.json")
    monkeypatch.setenv("ALLOW_LOCAL_AUTH", "false")

    with pytest.raises(RuntimeError, match="HTTPS"):
        auth.validate_bind_configuration()
