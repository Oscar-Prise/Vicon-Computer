from vicon_dssdk import ViconDataStream
from Header_NexusControl import CaptureNotifier
from Header_BertecControl import RemoteControl
from Header_JetsonControlDatastream_pertFull import StreamJetson
import argparse
import random
import time
import json
import threading

from utils_gait_seg import GaitSegmenter
from utils_rdVicon import connect_vicon, read_frame_signals

START_DELAY_S = 10
TRIAL_DURATION_S = 30
# Rolling window (cycles) for gait-phase estimation; typical range is 5-10.
GAIT_AVG_WINDOW_CYCLES = 5

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('host', nargs='?', help="Host name, in the format of server:port", default="localhost:801")
args = parser.parse_args()


def send_start_logging_signal(client_socket):
    start_signal = "START_LOGGING\n"
    client_socket.send(start_signal.encode('utf-8'))
    print("[SERVER] Sent start logging signal to client")


try:
    client = connect_vicon(args.host)

    def main():
        while True:
            bw = 67.6  # Body weight in (kg)

            # trial_number = int(input("Enter trial number: "))
            trial_name = input("Enter trial number: ")
            trial_notes = ""
            trial_description = ""
            trial_path = ""
            remote = RemoteControl()
            remote.start_connection()

            running = True

            print("\nPress OK in Bertec Software!\n")
            print("\nTrial name: ", trial_name)

            Jetson = StreamJetson("172.24.44.177", 11)
            server_thread = threading.Thread(target=Jetson.start_server, daemon=True)
            server_thread.start()
            print("Jetson server started in a separate thread.")

            print("Waiting for Jetson to connect...")
            while not Jetson.connection:
               time.sleep(0.1)
            print("Jetson connected successfully.")

            port_number = int(input("Input Port number: "))

            rand_id = random.randint(0, 2**32 - 1)
            Nexus_notifier = CaptureNotifier(
                name=trial_name, notes=trial_notes, description=trial_description,
                database_path=trial_path, delay_ms=0, packet_id=rand_id, port=port_number
            )

            print(f"\nTrial ready. Starting treadmill and data collection in {START_DELAY_S} seconds...")
            for remaining in range(START_DELAY_S, 0, -1):
                print(f"  {remaining}...")
                time.sleep(1)
            print("Starting trial now.\n")

            params = {
                'leftVel': '1.2', 'leftAccel': '0.5', 'leftDecel': '0.5',
                'rightVel': '1.2', 'rightAccel': '0.5', 'rightDecel': '0.5'
            }
            remote.run_treadmill(
                params['leftVel'], params['leftAccel'], params['leftDecel'],
                params['rightVel'], params['rightAccel'], params['rightDecel']
            )

            Nexus_notifier.notify()

            if Jetson.client_socket:
                send_start_logging_signal(Jetson.client_socket)
            else:
                print("[ERROR] No Jetson client socket available for start logging signal")

            segmenter = GaitSegmenter(avg_window_cycles=GAIT_AVG_WINDOW_CYCLES)
            segmenter.reset()
            timer_flag = 0
            while running:
                if timer_flag == 0:
                    start_time_trial = time.time()
                    timer_flag = 1
                elapsed_time_trial = time.time() - start_time_trial
                if elapsed_time_trial >= TRIAL_DURATION_S:
                    print(f"Stopping trial after {TRIAL_DURATION_S} seconds")
                    running = False
                    break

                signals = read_frame_signals(client)
                timestamp = time.time()
                segmenter.update_side(segmenter.right, signals.cop_r, signals.frz, timestamp)
                segmenter.update_side(segmenter.left, signals.cop_l, signals.flz, timestamp)

                # if segmenter.right.heel_strike:
                #     print("********RHS**************")
                # if segmenter.left.heel_strike:
                #     print("********LHS**************\n\n")

                try:
                    treadmill_data = {
                        "vicon_timestamp": timestamp,
                        # "copR": signals.cop_r,
                        # "copL": signals.cop_l,
                        # "Frz": signals.frz,
                        # "Flz": signals.flz,
                        "percent_gcR": segmenter.right.percent_gc,
                        "percent_gcL": segmenter.left.percent_gc,
                    }
                    treadmill_data_str = json.dumps(treadmill_data)
                    Jetson.send_data(treadmill_data_str)
                    # print(f"[DATA SENT] {treadmill_data_str}")
                except Exception as e:
                    print(f"[ERROR] Failed to send data: {e}")
                    break

            params = {
                'leftVel': '0', 'leftAccel': '0.5', 'leftDecel': '0.5',
                'rightVel': '0', 'rightAccel': '0.5', 'rightDecel': '0.5'
            }
            remote.run_treadmill(
                params['leftVel'], params['leftAccel'], params['leftDecel'],
                params['rightVel'], params['rightAccel'], params['rightDecel']
            )

            Nexus_notifier.close_socket()

            if Jetson.client_socket:
                Jetson.connection = False
                Jetson.client_socket.close()
                print("Jetson server closed.")

            print("Trial finished. Exiting experiment.")
            break
except ViconDataStream.DataStreamException as e:
    print('Handled data stream error', e)

if __name__ == "__main__":
    main()
