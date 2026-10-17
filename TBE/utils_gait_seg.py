"""Heel-strike gait segmentation from raw Vicon COP signals.

Heel strike is detected when COP transitions from 0 to a positive value.
The first heel strike per foot (standing contact at trial start) is ignored
for gait-cycle counting and averaging; counting begins on the second strike.
Gait phase (percent_gc) uses the mean cycle duration over the most recent
avg_window_cycles completed cycles (configurable, typically 5-10).
All input data is kept unprocessed (no abs, no normalization).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np


def detect_heel_strike(cop: float, prev_cop: float) -> bool:
    """Return True when COP crosses from 0 to a positive value."""
    return prev_cop == 0 and cop > 0


def is_on_plate(cop: float) -> bool:
    """Return True when COP indicates foot contact."""
    return cop > 0


@dataclass
class GaitSideState:
    """Runtime state for one foot."""

    prev_cop: float = 0.0
    initial_hs_seen: bool = False
    gc_count: int = 0
    time_gc: list[float] = field(default_factory=list)
    avg_time_gc: float = 0.0
    time_hs: float = 0.0
    percent_gc: float = 0.0
    heel_strike: bool = False
    on_plate: bool = False

    def reset(self) -> None:
        self.prev_cop = 0.0
        self.initial_hs_seen = False
        self.gc_count = 0
        self.time_gc = []
        self.avg_time_gc = 0.0
        self.time_hs = 0.0
        self.percent_gc = 0.0
        self.heel_strike = False
        self.on_plate = False


class GaitSegmenter:
    """Stateful heel-strike tracker for left and right feet."""

    def __init__(self, avg_window_cycles: int = 5) -> None:
        self.avg_window_cycles = avg_window_cycles
        self.right = GaitSideState()
        self.left = GaitSideState()

    def reset(self) -> None:
        self.right.reset()
        self.left.reset()

    def update_side(
        self,
        side: GaitSideState,
        cop: float,
        timestamp: float | None = None,
    ) -> None:
        """Update one foot from raw COP data."""
        if timestamp is None:
            timestamp = time.time()

        side.on_plate = is_on_plate(cop)

        if side.gc_count <= 1:
            side.avg_time_gc = 0.0
            side.percent_gc = 0.0
        elif side.avg_time_gc > 0:
            side.percent_gc = min(max((timestamp - side.time_hs) / side.avg_time_gc, 0.0), 1.0)
        else:
            side.percent_gc = 0.0

        side.heel_strike = detect_heel_strike(cop, side.prev_cop)
        side.prev_cop = cop

        if side.heel_strike:
            if not side.initial_hs_seen:
                # Skip standing contact at trial start (COP already on plate at t=0).
                side.initial_hs_seen = True
            elif side.gc_count == 0:
                side.gc_count += 1
                side.time_hs = timestamp
            else:
                side.gc_count += 1
                side.time_gc.append(timestamp - side.time_hs)
                side.time_hs = timestamp
                window = side.time_gc[-self.avg_window_cycles :]
                side.avg_time_gc = float(np.mean(window))
