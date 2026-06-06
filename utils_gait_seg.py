"""Heel-strike gait segmentation from raw Vicon COP signals.

Heel strike is detected when COP transitions from 0 to a positive value.
All input data is kept unprocessed (no abs, no normalization).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from utils_rdVicon import read_cop_from_vicon, read_grf_from_vicon


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
    gc_count: int = 0
    time_gc: list[float] = field(default_factory=list)
    avg_time_gc: float = 0.0
    time_hs: float = 0.0
    prev_time_hs: float = 0.0
    percent_gc: float = 0.0
    heel_strike: bool = False
    on_plate: bool = False
    cop: float = 0.0
    fz: float = 0.0

    def reset(self) -> None:
        self.prev_cop = 0.0
        self.gc_count = 0
        self.time_gc = []
        self.avg_time_gc = 0.0
        self.time_hs = 0.0
        self.prev_time_hs = 0.0
        self.percent_gc = 0.0
        self.heel_strike = False
        self.on_plate = False
        self.cop = 0.0
        self.fz = 0.0


class GaitSegmenter:
    """Stateful heel-strike tracker for left and right feet."""

    def __init__(self) -> None:
        self.right = GaitSideState()
        self.left = GaitSideState()

    def reset(self) -> None:
        self.right.reset()
        self.left.reset()

    def both_ready(self, min_cycles: int = 4) -> bool:
        return (
            self.right.gc_count >= min_cycles
            and self.left.gc_count >= min_cycles
        )

    def update_side(
        self,
        side: GaitSideState,
        cop: float,
        fz: float = 0.0,
        timestamp: float | None = None,
    ) -> None:
        """Update one foot from raw COP data."""
        if timestamp is None:
            timestamp = time.time()

        side.cop = cop
        side.fz = fz
        side.on_plate = is_on_plate(cop)

        if side.gc_count <= 1:
            side.avg_time_gc = 0.0
            side.percent_gc = 0.0
        elif side.avg_time_gc > 0:
            side.percent_gc = (timestamp - side.time_hs) / side.avg_time_gc
        else:
            side.percent_gc = 0.0

        side.heel_strike = detect_heel_strike(cop, side.prev_cop)
        side.prev_cop = cop

        if side.heel_strike:
            if side.gc_count == 0:
                side.gc_count += 1
                side.time_hs = timestamp
            else:
                side.gc_count += 1
                side.prev_time_hs = side.time_hs
                side.time_hs = timestamp
                side.time_gc.append(side.time_hs - side.prev_time_hs)
                side.avg_time_gc = float(np.mean(side.time_gc))

    def update_from_vicon(
        self,
        client,
        timestamp: float | None = None,
        plate_right: int = 1,
        plate_left: int = 2,
    ) -> None:
        """Read raw COP/GRF from a Vicon client and update state in one call."""
        cop_right, cop_left = read_cop_from_vicon(client)
        frz, flz = read_grf_from_vicon(client, plate_right=plate_right, plate_left=plate_left)
        self.update_side(self.right, cop_right, frz, timestamp)
        self.update_side(self.left, cop_left, flz, timestamp)
