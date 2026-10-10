"""Fail-closed framework for explicitly approved public web retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import ipaddress
from collections.abc import Callable, Mapping
from urllib.parse import urlparse


class ScrapeBlockedError(RuntimeError):
    """Raised when policy or the source blocks a public retrieval."""


@dataclass(frozen=True)
class ScraperPolicy:
    allowed_url_prefixes: tuple[str, ...]
    user_agent: str
    timeout_seconds: float = 10.0
    minimum_interval_seconds: float = 1.0
    max_retries: int = 2
    robots_allowed: bool = False
    terms_allowed: bool = False
    kill_switch: bool = False
    data_mode: str = "SCRAPED_PUBLIC"

    def validate(self) -> None:
        if not self.allowed_url_prefixes:
            raise ValueError("at least one allowed public URL prefix is required")
        if not self.user_agent.strip():
            raise ValueError("a descriptive user agent is required")
        if self.timeout_seconds <= 0 or self.minimum_interval_seconds < 0:
            raise ValueError("timeout and rate-limit settings are invalid")
        if self.max_retries < 0 or self.max_retries > 3:
            raise ValueError("max_retries must be between 0 and 3")
        if self.data_mode != "SCRAPED_PUBLIC":
            raise ValueError("public scraper must use SCRAPED_PUBLIC data mode")


@dataclass(frozen=True)
class FetchResponse:
    status_code: int
    body: bytes
    headers: Mapping[str, str]


@dataclass(frozen=True)
class ScrapeEnvelope:
    url: str
    retrieved_at: str
    payload_sha256: str
    payload_bytes: int
    status_code: int
    data_mode: str
    rights_state: str
    user_agent: str
    attempts: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class PublicScraper:
    def __init__(
        self,
        policy: ScraperPolicy,
        *,
        fetch: Callable[[str, float, str], FetchResponse],
        robots_checker: Callable[[str, str], bool],
        clock: Callable[[], float],
        sleep: Callable[[float], None],
        now: Callable[[], datetime] | None = None,
    ) -> None:
        policy.validate()
        self.policy = policy
        self._fetch = fetch
        self._robots_checker = robots_checker
        self._clock = clock
        self._sleep = sleep
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._last_fetch_at: float | None = None

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ScrapeBlockedError("only credential-free HTTPS public URLs are allowed")
        try:
            address = ipaddress.ip_address(parsed.hostname or "")
        except ValueError:
            address = None
        if address is not None and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
            raise ScrapeBlockedError("private or local target is not allowed")
        if not any(url.startswith(prefix) for prefix in self.policy.allowed_url_prefixes):
            raise ScrapeBlockedError("URL is outside configured public allow-list")

    def _wait_for_rate_limit(self) -> None:
        if self._last_fetch_at is None:
            return
        remaining = self.policy.minimum_interval_seconds - (self._clock() - self._last_fetch_at)
        if remaining > 0:
            self._sleep(remaining)

    def fetch_public(self, url: str) -> tuple[FetchResponse, ScrapeEnvelope]:
        self._validate_url(url)
        if self.policy.kill_switch:
            raise ScrapeBlockedError("public scraping kill switch is enabled")
        if not self.policy.robots_allowed or not self.policy.terms_allowed:
            raise ScrapeBlockedError("robots and terms permission are required before retrieval")
        if not self._robots_checker(url, self.policy.user_agent):
            raise ScrapeBlockedError("robots policy disallows retrieval")

        attempts = 0
        response: FetchResponse | None = None
        while attempts <= self.policy.max_retries:
            self._wait_for_rate_limit()
            attempts += 1
            self._last_fetch_at = self._clock()
            try:
                response = self._fetch(url, self.policy.timeout_seconds, self.policy.user_agent)
            except Exception as error:
                if attempts > self.policy.max_retries:
                    raise ScrapeBlockedError("retrieval failed after retry limit") from error
                continue
            if response.status_code in {401, 402, 403, 407, 408, 409, 451}:
                raise ScrapeBlockedError(f"source access blocked with HTTP {response.status_code}")
            if response.status_code == 429 or response.status_code >= 500:
                if attempts <= self.policy.max_retries:
                    continue
                raise ScrapeBlockedError(f"source remained unavailable with HTTP {response.status_code}")
            break
        if response is None or response.status_code < 200 or response.status_code >= 300:
            raise ScrapeBlockedError("source did not return a successful public response")
        retrieved_at = self._now()
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
            raise ValueError("scraper clock must return a timezone-aware timestamp")
        envelope = ScrapeEnvelope(
            url=url, retrieved_at=retrieved_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            payload_sha256=hashlib.sha256(response.body).hexdigest(), payload_bytes=len(response.body),
            status_code=response.status_code, data_mode=self.policy.data_mode, rights_state="UNASSESSED",
            user_agent=self.policy.user_agent, attempts=attempts,
        )
        return response, envelope
