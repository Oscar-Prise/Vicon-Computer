# TBE experiment, single-operator version: Vicon + Nexus + Bertec + Jetson in one script.
#
# Flow: Jetson connects -> Nexus port (if VICON_REC) -> enable motors -> countdown
# -> treadmill starts (+ Vicon starts recording) ->
# Vicon COP is streamed to the Jetson as gait-phase data for TRIAL_TIME_S
# -> treadmill stops (+ Vicon recording stops, saved as TRIAL_NAME).
#
# Usage: edit the parameters below, then run
#   python main_TBE.py

# ===================== Changeable parameters =====================
VICON_REC = True             # True: also record the trial in Vicon Nexus. False: no Nexus recording
                             # (the Vicon DataStream is still used for COP / gait phase either way)
TRIAL_NAME = "LG_1p2_ExoOn"  # Vicon trial name
NEXUS_PORT = None            # Nexus UDP trigger port; None = ask at runtime

START_DELAY_S = 15           # heads-up countdown before the treadmill starts (s)
TRIAL_TIME_S = 45            # how long the treadmill runs (s), ramp-up included

SPEED = 1.2                  # belt speed (m/s), both belts. Negative = backwards
ACCEL = 0.5                  # acceleration used to speed up (m/s^2)
DECEL = 0.5                  # deceleration used to stop at the end (m/s^2)

VICON_HOST = "localhost:801" # Vicon DataStream host, server:port
JETSON_IP = "172.24.44.177"  # IP this PC binds for the Jetson server
JETSON_PORT = 11
GAIT_AVG_WINDOW_CYCLES = 5   # rolling window (cycles) for gait-phase estimation; typical 5-10
# =================================================================

from vicon_dssdk import ViconDataStream
from Header_NexusControl import CaptureNotifier
from Header_BertecControl import BertecController
from Header_JetsonControlDatastream_pertFull import StreamJetson
from utils_gait_seg import GaitSegmenter
from utils_rdVicon import connect_vicon, read_frame_signals
import json
import random
import threading
import time


def set_treadmill(Bertec, left_vel, right_vel, accel, decel):
    """Send a one-shot Bertec speed command."""
    return Bertec.run_treadmill(str(left_vel), str(accel), str(decel),
                                str(right_vel), str(accel), str(decel))


def stop_treadmill(Bertec):
    print("\nTreadmill stop", flush=True)
    set_treadmill(Bertec, 0, 0, ACCEL, DECEL)


def send_start_logging_signal(client_socket):
    client_socket.send("START_LOGGING\n".encode('utf-8'))
    print("[SERVER] Sent start logging signal to client")


def main():
    try:
        client = connect_vicon(VICON_HOST)
    except ViconDataStream.DataStreamException as e:
        print('Handled data stream error', e)
        return

    Bertec = None
    Jetson = None
    Nexus_notifier = None
    recording = False
    try:
        Bertec = BertecController()
        if Bertec.start_connection() is None:
            print("Could not connect to Bertec. Is the Bertec software open with remote control enabled?")
            return
        print("\nPress OK in Bertec Software!\n")
        print(f"Treadmill: {SPEED} m/s for {TRIAL_TIME_S}s (accel {ACCEL}, decel {DECEL} m/s^2), "
              f"{START_DELAY_S}s heads-up")
        print(f"Vicon recording: {'ON, trial name ' + TRIAL_NAME if VICON_REC else 'OFF'}")

        Jetson = StreamJetson(JETSON_IP, JETSON_PORT)
        threading.Thread(target=Jetson.start_server, daemon=True).start()
        print("Jetson server started in a separate thread.")
        print("Waiting for Jetson to connect...")
        while not Jetson.connection:
            time.sleep(0.1)
        print("Jetson connected successfully.")

        if VICON_REC:
            # Port number must match the one in Nexus (use a new port if Nexus ignores a repeated trigger)
            port_number = NEXUS_PORT if NEXUS_PORT is not None else int(input("Input Nexus port number: "))
            Nexus_notifier = CaptureNotifier(
                name=TRIAL_NAME, notes="", description="", database_path="",
                delay_ms=0, packet_id=random.randint(0, 2**32 - 1), port=port_number
            )

        input(f"Activate motors, then press Enter to start the {START_DELAY_S}s heads-up...")
        for remaining in range(START_DELAY_S, 0, -1):
            print(f"  {remaining}...", flush=True)
            time.sleep(1)
        print("Heads-up finished. Starting treadmill.\n", flush=True)

        trial_start = time.time()
        set_treadmill(Bertec, SPEED, SPEED, ACCEL, DECEL)  # start the treadmill
        if VICON_REC:
            Nexus_notifier.notify()  # start Vicon recording
            recording = True
        if Jetson.client_socket:
            send_start_logging_signal(Jetson.client_socket)
        else:
            print("[ERROR] No Jetson client socket available for start logging signal")

        segmenter = GaitSegmenter(avg_window_cycles=GAIT_AVG_WINDOW_CYCLES)
        segmenter.reset()
        while True:
            if time.time() - trial_start >= TRIAL_TIME_S:
                print(f"Stopping trial after {TRIAL_TIME_S} seconds")
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
        # Always stop the belts and the Vicon capture, even on Ctrl+C or an error
        if Bertec is not None:
            stop_treadmill(Bertec)
            Bertec.stop_connection()
        if recording:
            Nexus_notifier.stop_capture()
        if Jetson is not None and Jetson.client_socket:
            Jetson.connection = False
            Jetson.client_socket.close()
            print("Jetson server closed.")


if __name__ == "__main__":
    main()
