"""Hype detection from chat *activity* (counts only, no usernames or text are stored)."""
from __future__ import annotations
import collections
import time

HYPE_WORDS = ("omg", "wtf", "clip", "pog", "kekw", "lul", "holy", "insane", "no way", "crazy")


def message_weight(text: str, keywords: tuple[str, ...]) -> float:
    """Normal message = 1. Hype words or GTA keywords count extra. Text is not kept."""
    t = text.lower()
    w = 1.0
    if any(k in t for k in HYPE_WORDS):
        w += 1.0
    if any(k.lower() in t for k in keywords):
        w += 1.0
    return w


class SpikeDetector:
    """Sliding window of weighted messages vs. slow-moving baseline."""

    def __init__(self, window=10.0, factor=3.0, min_score=25.0, cooldown=60.0, baseline_tau=300.0):
        self.window, self.factor, self.min_score = window, factor, min_score
        self.cooldown, self.tau = cooldown, baseline_tau
        self.events: collections.deque[tuple[float, float]] = collections.deque()
        self.baseline = 0.0  # weighted messages per window
        self.last_ts: float | None = None
        self.last_trigger = -1e18

    def _score(self, now: float) -> float:
        while self.events and self.events[0][0] < now - self.window:
            self.events.popleft()
        return sum(w for _, w in self.events)

    def add(self, weight: float, now: float | None = None) -> bool:
        """Register a message; return True if this triggers a clip."""
        now = time.time() if now is None else now
        self.events.append((now, weight))
        score = self._score(now)
        triggered = (
            score >= self.min_score
            and score >= self.factor * max(self.baseline, 1.0)
            and now - self.last_trigger >= self.cooldown
        )
        # update baseline slowly (not while spiking, so spikes don't raise their own bar)
        if self.last_ts is not None and not triggered:
            dt = max(now - self.last_ts, 0.0)
            alpha = min(dt / self.tau, 1.0)
            self.baseline += alpha * (score - self.baseline)
        self.last_ts = now
        if triggered:
            self.last_trigger = now
        return triggered
