# Heel-strike detection test: runs the treadmill and prints 3 on every RIGHT heel strike.
# No Nexus capture and no Jetson needed. Raw COP is saved to a CSV so you can
# check the detection afterwards.
#
# Usage:
#   python test_heel_strike.py                  # 1.2 m/s for 45 s after a 15 s countdown
#   python test_heel_strike.py --speed 1.0 --duration 30 --delay 10

from vicon_dssdk import ViconDataStream
from Header_BertecControl import BertecController
from treadmill_settings import DEFAULT_ACCEL, STOP_DECEL
from utils_gait_seg import GaitSegmenter
from utils_rdVicon import connect_vicon, read_frame_signals
import argparse
import csv
import time


def set_treadmill(Bertec, speed, accel, decel):
    return Bertec.run_treadmill(str(speed), str(accel), str(decel),
                                str(speed), str(accel), str(decel))


def main():
    parser = argparse.ArgumentParser(description="Print 3 on every right heel strike.")
    parser.add_argument("--speed", type=float, default=1.2, help="Belt speed (m/s)")
    parser.add_argument("--duration", type=int, default=45, help="Trial length (s)")
    parser.add_argument("--delay", type=int, default=15, help="Countdown before start (s)")
    parser.add_argument("--host", default="localhost:801", help="Vicon host, server:port")
    parser.add_argument("--csv", default="heel_strike_test.csv", help="Raw data output file")
    args = parser.parse_args()

    try:
        client = connect_vicon(args.host)
    except ViconDataStream.DataStreamException as e:
        print("Handled data stream error", e)
        return

    Bertec = BertecController()
    if Bertec.start_connection() is None:
        print("Could not connect to Bertec. Is the Bertec software open with remote control enabled?")
        return
    print("\nPress OK in Bertec Software if prompted!")

    try:
        input(f"\nPress Enter to start the {args.delay}s countdown...")
        for remaining in range(args.delay, 0, -1):
            print(f"  {remaining}...", flush=True)
            time.sleep(1)
        print("Starting treadmill now.\n", flush=True)

        set_treadmill(Bertec, args.speed, DEFAULT_ACCEL, STOP_DECEL)
        segmenter = GaitSegmenter()
        segmenter.reset()
        count = 0
        trial_start = time.time()

        with open(args.csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["t_s", "cop_r", "cop_l", "rhs", "lhs"])
            while time.time() - trial_start < args.duration:
                signals = read_frame_signals(client)
                now = time.time()
                segmenter.update_side(segmenter.right, signals.cop_r, now)
                segmenter.update_side(segmenter.left, signals.cop_l, now)

                if segmenter.right.heel_strike:
                    count += 1
                    print(3, flush=True)
                writer.writerow([f"{now - trial_start:.4f}", signals.cop_r, signals.cop_l,
                                 int(segmenter.right.heel_strike), int(segmenter.left.heel_strike)])
        print(f"\nTrial over. {count} right heel strikes detected. Raw data in {args.csv}")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("Treadmill stop", flush=True)
        set_treadmill(Bertec, 0, DEFAULT_ACCEL, STOP_DECEL)
        Bertec.stop_connection()


if __name__ == "__main__":
    main()
