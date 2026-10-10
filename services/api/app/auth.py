from fastapi import Header, HTTPException


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    """Fail closed until RIL-010 installs the scoped local owner-token verifier."""

    if not authorization or not authorization.startswith("Bearer ") or len(authorization) <= len("Bearer "):
        raise HTTPException(status_code=401, detail="bearer authentication is required")
    raise HTTPException(status_code=401, detail="owner authentication is not enabled yet")
