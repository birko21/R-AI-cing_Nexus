from threading import Event

import pytest

from app.worker_runtime import run_until_stopped


def test_worker_runtime_processes_bounded_steps_and_waits_when_idle() -> None:
    stop_event = Event()
    steps = iter(("job-1", None, "job-2"))
    waits: list[float] = []

    def wait(seconds: float) -> bool:
        waits.append(seconds)
        return False

    summary = run_until_stopped(
        lambda: next(steps),
        stop_event=stop_event,
        poll_seconds=2.5,
        max_jobs=2,
        wait=wait,
    )

    assert summary.jobs_processed == 2
    assert summary.idle_polls == 1
    assert summary.stop_requested is False
    assert waits == [2.5]


def test_worker_runtime_stops_without_dequeuing_after_signal() -> None:
    stop_event = Event()
    calls = 0

    def step() -> str:
        nonlocal calls
        calls += 1
        stop_event.set()
        return "job"

    summary = run_until_stopped(step, stop_event=stop_event, poll_seconds=1)

    assert calls == 1
    assert summary.jobs_processed == 1
    assert summary.stop_requested is True


@pytest.mark.parametrize(
    ("poll_seconds", "max_jobs"),
    ((0, None), (-1, None), (1, 0)),
)
def test_worker_runtime_rejects_invalid_limits(poll_seconds: float, max_jobs: int | None) -> None:
    with pytest.raises(ValueError):
        run_until_stopped(lambda: None, stop_event=Event(), poll_seconds=poll_seconds, max_jobs=max_jobs)
