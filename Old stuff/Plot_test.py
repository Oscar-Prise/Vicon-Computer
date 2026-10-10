"""Offline heel-strike segmentation test on output.csv using utils_gait_seg."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from utils_gait_seg import GaitSegmenter


def load_output_csv(csv_path: Path) -> dict[str, np.ndarray]:
    """Load output.csv columns: time_sent, time_recv, copR, copL, Frz, Flz."""
    data = np.loadtxt(csv_path, delimiter=",", ndmin=2)
    if data.shape[1] < 6:
        raise ValueError(f"Expected at least 6 columns, got {data.shape[1]}")

    time_sent = data[:, 0]
    time_recv = data[:, 1]
    cop_r = data[:, 2]
    cop_l = data[:, 3]
    frz = data[:, 4]
    flz = data[:, 5]

    keep = np.ones(len(data), dtype=bool)
    keep[1:] = np.any(
        np.column_stack([time_recv, cop_r, cop_l, frz, flz])[1:]
        != np.column_stack([time_recv, cop_r, cop_l, frz, flz])[:-1],
        axis=1,
    )

    time = time_recv[keep] - time_recv[keep][0]

    return {
        "time": time,
        "cop_r": cop_r[keep],
        "cop_l": cop_l[keep],
        "frz": frz[keep],
        "flz": flz[keep],
        "time_sent": time_sent[keep],
        "time_recv": time_recv[keep],
    }


def segment_gait(data: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Run GaitSegmenter over the loaded CSV data."""
    segmenter = GaitSegmenter()
    segmenter.reset()

    n = len(data["time"])
    heel_strike_r = np.zeros(n, dtype=bool)
    heel_strike_l = np.zeros(n, dtype=bool)
    on_plate_r = np.zeros(n, dtype=bool)
    on_plate_l = np.zeros(n, dtype=bool)
    percent_gc_r = np.zeros(n)
    percent_gc_l = np.zeros(n)
    gc_count_r = np.zeros(n, dtype=int)
    gc_count_l = np.zeros(n, dtype=int)

    for i in range(n):
        timestamp = float(data["time_recv"][i])
        segmenter.update_side(segmenter.right, float(data["cop_r"][i]), float(data["frz"][i]), timestamp)
        segmenter.update_side(segmenter.left, float(data["cop_l"][i]), float(data["flz"][i]), timestamp)
        heel_strike_r[i] = segmenter.right.heel_strike
        heel_strike_l[i] = segmenter.left.heel_strike
        on_plate_r[i] = segmenter.right.on_plate
        on_plate_l[i] = segmenter.left.on_plate
        percent_gc_r[i] = segmenter.right.percent_gc
        percent_gc_l[i] = segmenter.left.percent_gc
        gc_count_r[i] = segmenter.right.gc_count
        gc_count_l[i] = segmenter.left.gc_count

    return {
        "heel_strike_r": heel_strike_r,
        "heel_strike_l": heel_strike_l,
        "on_plate_r": on_plate_r,
        "on_plate_l": on_plate_l,
        "percent_gc_r": percent_gc_r,
        "percent_gc_l": percent_gc_l,
        "gc_count_r": gc_count_r,
        "gc_count_l": gc_count_l,
    }


def summarize_heel_strikes(
    time: np.ndarray,
    heel_strike: np.ndarray,
    side_name: str,
) -> list[tuple[str, float]]:
    events: list[tuple[str, float]] = []
    for t, is_hs in zip(time, heel_strike):
        if is_hs:
            events.append((f"{side_name} heel strike", float(t)))
    return events


def plot_results(
    data: dict[str, np.ndarray],
    segmented: dict[str, np.ndarray],
    output_path: Path,
    show: bool,
) -> None:
    time = data["time"]
    events_r = summarize_heel_strikes(time, segmented["heel_strike_r"], "Right")
    events_l = summarize_heel_strikes(time, segmented["heel_strike_l"], "Left")

    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

    axes[0].plot(time, data["cop_r"], label="copR", color="#1f77b4", linewidth=1.2)
    axes[0].plot(time, data["cop_l"], label="copL", color="#ff7f0e", linewidth=1.2)
    axes[0].axhline(0, color="gray", linestyle=":", linewidth=1)
    axes[0].set_ylabel("COP (raw Cy)")
    axes[0].set_title("Raw COP signals")
    axes[0].legend(loc="upper right")
    axes[0].grid(True, alpha=0.3)

    for label, t in events_r + events_l:
        color = "#1f77b4" if label.startswith("Right") else "#ff7f0e"
        for ax in axes:
            ax.axvline(t, color=color, linestyle="-", alpha=0.25, linewidth=1)

    axes[1].step(
        time,
        segmented["on_plate_r"].astype(int),
        where="post",
        label="copR > 0",
        color="#1f77b4",
    )
    axes[1].step(
        time,
        segmented["on_plate_l"].astype(int),
        where="post",
        label="copL > 0",
        color="#ff7f0e",
    )
    axes[1].set_yticks([0, 1])
    axes[1].set_yticklabels(["off plate", "on plate"])
    axes[1].set_ylabel("Contact")
    axes[1].set_title("Foot contact (COP > 0)")
    axes[1].legend(loc="upper right")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(time, segmented["percent_gc_r"], label="% gait cycle R", color="#1f77b4")
    axes[2].plot(time, segmented["percent_gc_l"], label="% gait cycle L", color="#ff7f0e")
    axes[2].axhline(1.0, color="gray", linestyle=":", linewidth=1)
    axes[2].set_ylabel("% GC")
    axes[2].set_title("Percent through current gait cycle (heel strike to heel strike)")
    axes[2].legend(loc="upper right")
    axes[2].grid(True, alpha=0.3)

    axes[3].plot(time, segmented["gc_count_r"], label="heel-strike count R", color="#1f77b4")
    axes[3].plot(time, segmented["gc_count_l"], label="heel-strike count L", color="#ff7f0e")
    axes[3].set_xlabel("Time since start (s)")
    axes[3].set_ylabel("Heel-strike count")
    axes[3].set_title("Cumulative heel-strike count")
    axes[3].legend(loc="upper left")
    axes[3].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    print(f"Saved plot to {output_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def print_summary(data: dict[str, np.ndarray], segmented: dict[str, np.ndarray]) -> None:
    duration = float(data["time"][-1] - data["time"][0])
    final_gc_r = int(segmented["gc_count_r"][-1])
    final_gc_l = int(segmented["gc_count_l"][-1])

    print(f"Samples used: {len(data['time'])}")
    print(f"Duration: {duration:.2f} s")
    print(f"Right heel strikes detected: {final_gc_r}")
    print(f"Left heel strikes detected: {final_gc_l}")
    print(f"Right on-plate frames (cop > 0): {int(np.sum(segmented['on_plate_r']))}")
    print(f"Left on-plate frames (cop > 0): {int(np.sum(segmented['on_plate_l']))}")

    print("\nFirst heel strikes:")
    for label, t in summarize_heel_strikes(data["time"], segmented["heel_strike_r"], "Right")[:5]:
        print(f"  {t:8.3f}s  {label}")
    for label, t in summarize_heel_strikes(data["time"], segmented["heel_strike_l"], "Left")[:5]:
        print(f"  {t:8.3f}s  {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).parent / "output.csv",
        help="Path to output.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "gait_segmentation_plot.png",
        help="Path to save the plot image",
    )
    parser.add_argument("--show", action="store_true", help="Display the plot interactively")
    args = parser.parse_args()

    data = load_output_csv(args.csv)
    segmented = segment_gait(data)
    print_summary(data, segmented)
    plot_results(data, segmented, args.output, show=args.show)


if __name__ == "__main__":
    main()
