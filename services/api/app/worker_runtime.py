"""Small, signal-safe runtime for durable ingestion consumers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Event
from typing import TypeVar


StepResult = TypeVar("StepResult")


@dataclass(frozen=True)
class WorkerLoopSummary:
    """Counters emitted when a consumer loop exits cooperatively."""

    jobs_processed: int
    idle_polls: int
    stop_requested: bool


def run_until_stopped(
    step: Callable[[], StepResult | None],
    *,
    stop_event: Event,
    poll_seconds: float,
    max_jobs: int | None = None,
    wait: Callable[[float], bool] | None = None,
) -> WorkerLoopSummary:
    """Run bounded steps until shutdown, an optional cap, or test completion.

    ``step`` must finish one bounded unit of work and return ``None`` when the
    queue is empty. ``Event.wait`` is used instead of ``time.sleep`` so a
    SIGTERM handler can wake an idle worker immediately. Signal handlers should
    only set ``stop_event``; the current bounded step is then allowed to finish
    before the loop stops dequeuing new work.
    """

    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive")
    if max_jobs is not None and max_jobs < 1:
        raise ValueError("max_jobs must be positive when provided")

    wait_for_stop = wait or stop_event.wait
    jobs_processed = 0
    idle_polls = 0
    while not stop_event.is_set() and (max_jobs is None or jobs_processed < max_jobs):
        result = step()
        if result is None:
            idle_polls += 1
            wait_for_stop(poll_seconds)
            continue
        jobs_processed += 1

    return WorkerLoopSummary(
        jobs_processed=jobs_processed,
        idle_polls=idle_polls,
        stop_requested=stop_event.is_set(),
    )
