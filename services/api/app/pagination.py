from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

from fastapi import HTTPException, Query


def paging_parameters(
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = Query(default=None),
    as_of: datetime | None = Query(default=None),
) -> tuple[int, str | None, datetime]:
    effective_as_of = as_of or datetime.now(timezone.utc)
    if effective_as_of.tzinfo is None or effective_as_of.utcoffset() is None:
        raise HTTPException(status_code=400, detail="as_of must include a timezone offset")
    if cursor is not None:
        decode_cursor(cursor, effective_as_of)
    return limit, cursor, effective_as_of.astimezone(timezone.utc)


def _cursor_key() -> bytes:
    return os.environ.get("CURSOR_SIGNING_KEY", "local-development-cursor-key").encode("utf-8")


def encode_cursor(as_of: datetime, offset: int, filters: dict[str, str]) -> str:
    payload = json.dumps(
        {"as_of": as_of.astimezone(timezone.utc).isoformat(), "offset": offset, "filters": filters},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    signature = hmac.new(_cursor_key(), payload, hashlib.sha256).digest()
    return ".".join(
        base64.urlsafe_b64encode(part).decode("ascii").rstrip("=") for part in (payload, signature)
    )


def decode_cursor(cursor: str, as_of: datetime) -> dict[str, object]:
    try:
        encoded_payload, encoded_signature = cursor.split(".", 1)
        payload = base64.urlsafe_b64decode(encoded_payload + "===")
        signature = base64.urlsafe_b64decode(encoded_signature + "===")
        expected = hmac.new(_cursor_key(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        parsed = json.loads(payload)
        if parsed.get("as_of") != as_of.astimezone(timezone.utc).isoformat():
            raise ValueError("cursor as_of mismatch")
        if not isinstance(parsed.get("offset"), int) or parsed["offset"] < 0:
            raise ValueError("invalid offset")
        return parsed
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="cursor is invalid or bound to different filters") from exc
