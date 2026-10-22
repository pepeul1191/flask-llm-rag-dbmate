# ai/pipeline/timing.py
import time
import statistics
from contextlib import contextmanager
from typing import Dict, Any


class TimingCollector:
    def __init__(self):
        self.records: Dict[str, list[float]] = {}
        self._t0 = time.perf_counter()

    @contextmanager
    def time(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.records.setdefault(name, []).append(elapsed)

    def total_seconds(self) -> float:
        return time.perf_counter() - self._t0

    def summary(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for name, samples in self.records.items():
            out[name] = _stats(samples)
        out["__total__"] = {"seconds": round(self.total_seconds(), 3)}
        return out


def _stats(samples: list[float]) -> Dict[str, float]:
    if not samples:
        return {}
    n = len(samples)
    mean = statistics.fmean(samples)
    out = {
        "seconds_mean": round(mean, 3),
        "seconds_total": round(sum(samples), 3),
        "n_runs": n,
    }
    if n >= 2:
        out["seconds_std"] = round(statistics.pstdev(samples), 3)
        k = max(0, int(round(0.95 * (n - 1))))
        out["seconds_p95"] = round(sorted(samples)[k], 3)
    return out