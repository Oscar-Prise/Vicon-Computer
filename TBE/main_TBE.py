# TBE experiment, single-operator version: Vicon + Nexus + Bertec + Jetson in one script.
#
# Condition: walk 45 s at 1.2 m/s (LG_1p2_ExoOn).
# Flow: Jetson connects -> Nexus port -> enable motors -> 15 s heads-up countdown
# -> treadmill starts and Vicon starts recording together ->
# Vicon COP is streamed to the Jetson as gait-phase data -> treadmill stops.
#
# Usage:
#   python main_TBE.py                       # 45 s at 1.2 m/s, 15 s heads-up
#   python main_TBE.py --list
#   python main_TBE.py --host localhost:801 --jetson-ip 172.24.44.177

from vicon_dssdk import ViconDataStream
from Header_NexusControl import CaptureNotifier
from Header_BertecControl import BertecController
from Header_JetsonControlDatastream_pertFull import StreamJetson
from treadmill_settings import SETTINGS, DEFAULT_ACCEL, DEFAULT_DECEL, STOP_DECEL
from utils_gait_seg import GaitSegmenter
from utils_rdVicon import connect_vicon, read_frame_signals
import argparse
import json
import random
import threading
import time

START_DELAY_S = 15  # heads-up before the belts and Vicon recording start
TRIAL_NAME = "LG_1p2_ExoOn"
JETSON_IP = "172.24.44.177"
JETSON_PORT = 11
# Rolling window (cycles) for gait-phase estimation; typical range is 5-10.
GAIT_AVG_WINDOW_CYCLES = 5


def set_treadmill(Bertec, left_vel, right_vel, accel, decel):
    """Send a one-shot Bertec speed command."""
    return Bertec.run_treadmill(str(left_vel), str(accel), str(decel),
                                str(right_vel), str(accel), str(decel))


def stop_treadmill(Bertec):
    print("\nTreadmill stop", flush=True)
    set_treadmill(Bertec, 0, 0, DEFAULT_ACCEL, STOP_DECEL)


def send_start_logging_signal(client_socket):
    client_socket.send("START_LOGGING\n".encode('utf-8'))
    print("[SERVER] Sent start logging signal to client")


class ProfileRunner:
    """Steps through treadmill segments by elapsed time without blocking the Vicon loop."""

    def __init__(self, Bertec, segments):
        self.Bertec = Bertec
        self.segments = segments
        self.total = sum(seg["duration"] for seg in segments)
        self.idx = -1
        self.next_change = 0.0

    def update(self, elapsed):
        """Send the next segment command when due. Returns False once the profile is over."""
        if elapsed >= self.total:
            return False
        if elapsed >= self.next_change:
            self.idx += 1
            seg = self.segments[self.idx]
            left = seg.get("left", seg.get("speed"))
            right = seg.get("right", seg.get("speed"))
            accel = seg.get("accel", DEFAULT_ACCEL)
            decel = seg.get("decel", DEFAULT_DECEL)
            print(f"[{elapsed:6.1f}s] Segment {self.idx + 1}/{len(self.segments)}: "
                  f"L={left} m/s, R={right} m/s for {seg['duration']}s", flush=True)
            set_treadmill(self.Bertec, left, right, accel, decel)
            self.next_change += seg["duration"]
        return True


def main():
    parser = argparse.ArgumentParser(description="TBE experiment with treadmill profile and start delay.")
    parser.add_argument("setting", nargs="?", default="default", help="Setting name from treadmill_settings.py")
    parser.add_argument("--delay", type=int, default=START_DELAY_S, help="Countdown before start (s)")
    parser.add_argument("--host", default="localhost:801", help="Vicon host, server:port")
    parser.add_argument("--jetson-ip", default=JETSON_IP, help="IP this PC binds for the Jetson server")
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

    try:
        client = connect_vicon(args.host)
    except ViconDataStream.DataStreamException as e:
        print('Handled data stream error', e)
        return

    Bertec = None
    Jetson = None
    Nexus_notifier = None
    try:
        trial_name = TRIAL_NAME

        Bertec = BertecController()
        if Bertec.start_connection() is None:
            print("Could not connect to Bertec. Is the Bertec software open with remote control enabled?")
            return
        print("\nPress OK in Bertec Software!\n")
        print("Trial name:", trial_name)
        walk_s = sum(seg["duration"] for seg in segments)
        print(f"Walk {walk_s}s at 1.2 m/s, {args.delay}s heads-up")
        print(f"Setting: {args.setting}")
        for i, seg in enumerate(segments):
            print(f"  {i + 1}. {seg}")

        Jetson = StreamJetson(args.jetson_ip, JETSON_PORT)
        threading.Thread(target=Jetson.start_server, daemon=True).start()
        print("Jetson server started in a separate thread.")
        print("Waiting for Jetson to connect...")
        while not Jetson.connection:
            time.sleep(0.1)
        print("Jetson connected successfully.")

        port_number = int(input("Input Port number: "))
        Nexus_notifier = CaptureNotifier(
            name=trial_name, notes="", description="", database_path="",
            delay_ms=0, packet_id=random.randint(0, 2**32 - 1), port=port_number
        )

        input(f"Activate motors, then press Enter to start the {args.delay}s heads-up...")
        for remaining in range(args.delay, 0, -1):
            print(f"  {remaining}...", flush=True)
            time.sleep(1)
        print("Heads-up finished. Starting treadmill and Vicon recording.\n", flush=True)

        profile = ProfileRunner(Bertec, segments)
        trial_start = time.time()
        profile.update(0.0)  # start the treadmill
        Nexus_notifier.notify()  # start Vicon recording
        if Jetson.client_socket:
            send_start_logging_signal(Jetson.client_socket)
        else:
            print("[ERROR] No Jetson client socket available for start logging signal")

        segmenter = GaitSegmenter(avg_window_cycles=GAIT_AVG_WINDOW_CYCLES)
        segmenter.reset()
        while True:
            elapsed = time.time() - trial_start
            if not profile.update(elapsed):
                print(f"Stopping trial after {profile.total} seconds")
                break

            signals = read_frame_signals(client)
            timestamp = time.time()
            segmenter.update_side(segmenter.right, signals.cop_r, timestamp)
            segmenter.update_side(segmenter.left, signals.cop_l, timestamp)

            try:
                # percent_gc plus COP contact events for the Phase Variable on the Jetson
                treadmill_data = {
                    "vicon_timestamp": timestamp,
                    "percent_gcR": segmenter.right.percent_gc,
                    "percent_gcL": segmenter.left.percent_gc,
                    "on_plateR": segmenter.right.on_plate,
                    "on_plateL": segmenter.left.on_plate,
                    "heel_strikeR": segmenter.right.heel_strike,
                    "heel_strikeL": segmenter.left.heel_strike,
                }
                Jetson.send_data(json.dumps(treadmill_data))
            except Exception as e:
                print(f"[ERROR] Failed to send data: {e}")
                break
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Always stop the belts, even on Ctrl+C or an error
        if Bertec is not None:
            stop_treadmill(Bertec)
            Bertec.stop_connection()
        if Nexus_notifier is not None:
            Nexus_notifier.close_socket()
        if Jetson is not None and Jetson.client_socket:
            Jetson.connection = False
            Jetson.client_socket.close()
            print("Jetson server closed.")
        print("Trial finished. Exiting experiment.")


if __name__ == "__main__":
    main()
