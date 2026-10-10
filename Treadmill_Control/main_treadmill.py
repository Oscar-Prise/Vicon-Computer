# Run the Bertec treadmill with a countdown delay, using a profile from treadmill_settings.py
#
# Usage:
#   python main_treadmill.py                 # runs the "default" setting
#   python main_treadmill.py steps           # runs the "steps" setting
#   python main_treadmill.py default --delay 10
#   python main_treadmill.py --list          # show available settings

from Header_BertecControl import BertecController
from treadmill_settings import SETTINGS, DEFAULT_ACCEL, DEFAULT_DECEL, STOP_DECEL
import argparse
import time

START_DELAY_S = 15


def set_treadmill(Bertec, left_vel, right_vel, accel, decel):
    """Send a one-shot Bertec speed command."""
    return Bertec.run_treadmill(str(left_vel), str(accel), str(decel),
                                str(right_vel), str(accel), str(decel))


def stop_treadmill(Bertec):
    print("\nTreadmill stop", flush=True)
    set_treadmill(Bertec, 0, 0, DEFAULT_ACCEL, STOP_DECEL)


def run_setting(Bertec, segments):
    trial_start = time.time()
    for i, seg in enumerate(segments):
        left = seg.get("left", seg.get("speed"))
        right = seg.get("right", seg.get("speed"))
        accel = seg.get("accel", DEFAULT_ACCEL)
        decel = seg.get("decel", DEFAULT_DECEL)
        duration = seg["duration"]

        print(f"[{time.time() - trial_start:6.1f}s] Segment {i + 1}/{len(segments)}: "
              f"L={left} m/s, R={right} m/s for {duration}s", flush=True)
        set_treadmill(Bertec, left, right, accel, decel)
        time.sleep(duration)


def main():
    parser = argparse.ArgumentParser(description="Run the Bertec treadmill with a start delay.")
    parser.add_argument("setting", nargs="?", default="default", help="Setting name from treadmill_settings.py")
    parser.add_argument("--delay", type=int, default=START_DELAY_S, help="Countdown before start (s)")
    parser.add_argument("--list", action="store_true", help="List available settings and exit")
    args = parser.parse_args()

    if args.list:
        for name, segments in SETTINGS.items():
            total = sum(seg["duration"] for seg in segments)
            print(f"  {name}: {len(segments)} segment(s), {total}s total")
        return

    if args.setting not in SETTINGS:
        print(f"Unknown setting '{args.setting}'. Available: {', '.join(SETTINGS)}")
        return
    segments = SETTINGS[args.setting]

    # Create an instance of BertecControl
    Bertec = BertecController()
    res = Bertec.start_connection()
    if res is None:
        print("Could not connect to Bertec. Is the Bertec software open with remote control enabled?")
        return

    print(f"\nSetting: {args.setting}")
    for i, seg in enumerate(segments):
        print(f"  {i + 1}. {seg}")
    print("\nPress OK in Bertec Software if prompted!")

    try:
        input(f"\nPress Enter to start the {args.delay}s countdown...")
        for remaining in range(args.delay, 0, -1):
            print(f"  {remaining}...", flush=True)
            time.sleep(1)
        print("Starting treadmill now.\n", flush=True)

        run_setting(Bertec, segments)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Always stop the belts, even on Ctrl+C or an error
        stop_treadmill(Bertec)
        Bertec.stop_connection()
        print("Done.")


if __name__ == "__main__":
    main()
