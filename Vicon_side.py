from vicon_dssdk import ViconDataStream
from Header_NexusControl import CaptureNotifier
from Header_BertecControl import RemoteControl
from Header_JetsonControlDatastream_pertFull import StreamJetson
import argparse
import sys
import numpy as np
import random
import time
import json
import threading


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('host', nargs='?', help="Host name, in the format of server:port", default="localhost:801")
args = parser.parse_args()

client = ViconDataStream.Client()


def send_start_logging_signal(client_socket):
    start_signal = "START_LOGGING\n"
    client_socket.send(start_signal.encode('utf-8'))
    print("[SERVER] Sent start logging signal to client")


try:
    client.Connect(args.host)
    client.SetBufferSize(1)
    client.EnableDeviceData()

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

            params = {
                'leftVel': '0', 'leftAccel': '0.5', 'leftDecel': '0.5',
                'rightVel': '0', 'rightAccel': '0.5', 'rightDecel': '0.5'
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

            timer_flag = 0
            while running:
                if timer_flag == 0:
                    start_time_trial = time.time()
                    timer_flag = 1
                elapsed_time_trial = time.time() - start_time_trial
                if elapsed_time_trial >= 30:
                    print("Stopping trial after 30 seconds")
                    running = False
                    break

                HasFrame = False
                timeout = 50
                while not HasFrame:
                    try:
                        if client.GetFrame():
                            HasFrame = True
                        timeout -= 1
                        if timeout < 0:
                            print('Failed to get frame')
                            sys.exit()
                    except ViconDataStream.DataStreamException:
                        client.GetFrame()
                client.SetStreamMode(ViconDataStream.Client.StreamMode.EServerPush)

                copR, copL = 0, 0
                devices = client.GetDeviceNames()
                for deviceName, deviceType in devices:
                    deviceOutputDetails = client.GetDeviceOutputDetails(deviceName)
                    for outputName, componentName, unit in deviceOutputDetails:
                        if componentName == "Cy":
                            values, occluded = client.GetDeviceOutputValues(deviceName, outputName, componentName)
                            if deviceName == "Right":
                                copR = np.abs(values[0])
                            elif deviceName == "Left":
                                copL = np.abs(values[0])

                Flz, Frz, Flznorm, Frznorm = 0, 0, 0, 0
                forceplates = client.GetForcePlates()
                for plate in forceplates:
                    globalForceVectorData = client.GetGlobalForceVector(plate)
                    if plate == 1:
                        Frz = abs(globalForceVectorData[0][2])
                        Frznorm = Frz / (bw * 10)
                    if plate == 2:
                        Flz = abs(globalForceVectorData[0][2])
                        Flznorm = Flz / (bw * 10)

                try:
                    treadmill_data = {
                        "vicon_timestamp": time.time(),
                        "copR": copR,
                        "copL": copL,
                        "Frznorm": Frznorm,
                        "Flznorm": Flznorm,
                    }
                    treadmill_data_str = json.dumps(treadmill_data)
                    Jetson.send_data(treadmill_data_str)
                    print(f"[DATA SENT] {treadmill_data_str}")
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
