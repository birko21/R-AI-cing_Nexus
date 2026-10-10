from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.scraping import FetchResponse, PublicScraper, ScrapeBlockedError, ScraperPolicy


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.value

    def sleep(self, duration: float) -> None:
        self.sleeps.append(duration)
        self.value += duration


def policy(**kwargs: object) -> ScraperPolicy:
    options = {"robots_allowed": True, "terms_allowed": True, **kwargs}
    return ScraperPolicy(("https://public.example/racing/",), "RacingIntelligenceLab/0.1 (+research@example.invalid)", **options)


def scraper(responses: list[FetchResponse], **kwargs: object) -> tuple[PublicScraper, list[tuple[str, float, str]], FakeClock]:
    calls: list[tuple[str, float, str]] = []
    clock = FakeClock()
    queue = list(responses)

    def fetch(url: str, timeout: float, user_agent: str) -> FetchResponse:
        calls.append((url, timeout, user_agent))
        return queue.pop(0)

    return PublicScraper(policy(**kwargs), fetch=fetch, robots_checker=lambda url, ua: True, clock=clock.now, sleep=clock.sleep, now=lambda: datetime(2026, 1, 15, tzinfo=timezone.utc)), calls, clock


def test_mock_public_site_fetch_is_policy_bound_and_provenanced() -> None:
    subject, calls, _ = scraper([FetchResponse(200, b"mock-race", {"content-type": "text/plain"})], minimum_interval_seconds=0)

    response, envelope = subject.fetch_public("https://public.example/racing/race-1")

    assert response.body == b"mock-race"
    assert calls == [("https://public.example/racing/race-1", 10.0, "RacingIntelligenceLab/0.1 (+research@example.invalid)")]
    assert envelope.data_mode == "SCRAPED_PUBLIC"
    assert envelope.rights_state == "UNASSESSED"
    assert envelope.attempts == 1
    assert envelope.payload_bytes == len(b"mock-race")


def test_rate_limit_retry_and_timeout_are_enforced() -> None:
    subject, calls, clock = scraper([FetchResponse(503, b"busy", {}), FetchResponse(200, b"ok", {})], max_retries=1, minimum_interval_seconds=2)

    subject.fetch_public("https://public.example/racing/race-1")

    assert len(calls) == 2
    assert clock.sleeps == [2.0]


@pytest.mark.parametrize("url", [
    "https://other.example/race",
    "http://public.example/racing/race",
    "https://user:password@public.example/racing/race",
    "https://127.0.0.1/racing/race",
])
def test_target_validation_never_allows_unapproved_or_private_access(url: str) -> None:
    subject, _, _ = scraper([FetchResponse(200, b"unexpected", {})])

    with pytest.raises(ScrapeBlockedError):
        subject.fetch_public(url)


def test_robots_terms_and_kill_switch_fail_closed() -> None:
    subject, _, _ = scraper([FetchResponse(200, b"unexpected", {})], robots_allowed=False)
    with pytest.raises(ScrapeBlockedError, match="robots and terms"):
        subject.fetch_public("https://public.example/racing/race")

    subject, _, _ = scraper([FetchResponse(200, b"unexpected", {})], kill_switch=True)
    with pytest.raises(ScrapeBlockedError, match="kill switch"):
        subject.fetch_public("https://public.example/racing/race")


def test_auth_paywall_and_antibot_responses_are_not_retried_or_bypassed() -> None:
    subject, calls, _ = scraper([FetchResponse(403, b"blocked", {})], max_retries=3)

    with pytest.raises(ScrapeBlockedError, match="HTTP 403"):
        subject.fetch_public("https://public.example/racing/race")
    assert len(calls) == 1


def test_retry_limit_on_transport_failure_is_bounded() -> None:
    class Failing:
        def __call__(self, url: str, timeout: float, user_agent: str) -> FetchResponse:
            raise TimeoutError("mock timeout")

    clock = FakeClock()
    subject = PublicScraper(policy(max_retries=2), fetch=Failing(), robots_checker=lambda url, ua: True, clock=clock.now, sleep=clock.sleep)

    with pytest.raises(ScrapeBlockedError, match="retry limit"):
        subject.fetch_public("https://public.example/racing/race")
