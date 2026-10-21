"""
Optional token and cost accounting for structured LLM calls.

Inert unless a `UsageTracker` is installed for the current task (`with track_usage() as u:`), so
the existing managers and scripts behave exactly as before. The specialist-loss runner installs one
per run to report tokens and cost.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class UsageTracker:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    by_model: dict[str, dict[str, float]] = field(default_factory=dict)

    def add(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        cost = _cost(model, prompt_tokens, completion_tokens)
        self.calls += 1
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.cost_usd += cost
        m = self.by_model.setdefault(model, {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0})
        m["calls"] += 1
        m["prompt_tokens"] += prompt_tokens
        m["completion_tokens"] += completion_tokens
        m["cost_usd"] += cost

    def snapshot(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": self.cost_usd,
        }


_current: ContextVar[UsageTracker | None] = ContextVar("llm_usage_tracker", default=None)


@contextmanager
def track_usage() -> Iterator[UsageTracker]:
    tracker = UsageTracker()
    token = _current.set(tracker)
    try:
        yield tracker
    finally:
        _current.reset(token)


def record_usage(model: str, result: Any) -> None:
    """Record one call's tokens if a tracker is installed. `result` is the Instructor-parsed object,
    which keeps the raw completion in `_raw_response`."""
    tracker = _current.get()
    if tracker is None:
        return
    usage = getattr(getattr(result, "_raw_response", None), "usage", None)
    tracker.add(model, int(getattr(usage, "prompt_tokens", 0) or 0), int(getattr(usage, "completion_tokens", 0) or 0))


def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    try:
        from litellm.cost_calculator import cost_per_token

        p, c = cost_per_token(model=model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        return float(p + c)
    except Exception:
        return 0.0
