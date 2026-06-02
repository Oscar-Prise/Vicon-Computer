#for multiple perturbation trials May2 development
from vicon_dssdk import ViconDataStream
from Header_NexusControl import CaptureNotifier
from Header_BertecControl import RemoteControl
from Header_JetsonControlDatastream_pertFull import StreamJetson
import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import random
import csv
import time
from time import sleep
import json
import threading
import re


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('host', nargs='?', help="Host name, in the format of server:port", default = "localhost:801")
args = parser.parse_args()


global  GRFl, GRFr, Frz, Frl, copR, copL, prev_COP_r, prev_COP_l, phaseR, phaseL, pert_flag, current_global_frame, Flz, Flznorm, Frznorm

client = ViconDataStream.Client()
pert_flag = 0
GRFr = []
GRFl = []
gc_countR = 0
gc_countL = 0
time_gcR = []
time_gcL = []

#Calculate gait cycle    
def determine_phase_grf_cop(Fznorm, prev_fznorm,cop, prev_cop,avg_time_gc,percent_gc):
    """Helper function to determine the phase for a given side."""

    if cop > 0 and prev_cop == 0:
        return 2 #heel strike
    
    elif avg_time_gc !=0 and prev_cop >0 and cop == 0 : #and prev_fznorm>Fznorm:
        return 3  # toe-off
        
    elif cop> 0 and prev_cop > 0:
        return 1 #stance
    else:
        return 0 #swing

def send_start_logging_signal(client_socket):
    start_signal = "START_LOGGING\n"
    client_socket.send(start_signal.encode('utf-8'))
    print("[SERVER] Sent start logging signal to client")


try:
    client.Connect( args.host )
    client.SetBufferSize( 1 )
    client.EnableDeviceData()

    def main():

        while True:
            global gc_countR,gc_countL, pert_flag, current_global_frame,bw, time_hsR, time_gcR, prev_time_hsR, time_hsL, time_gcL, prev_time_hsL 
            gc_countR = 0
            gc_countL = 0
            pert_times_list = []
            bw = 67.6
             # Body weight in (kg)
            speed = "1p25"
        
            trial_number = int(input("Enter trial number: "))
            trial_name = f"{trial_number}"
            trial_notes = ""
            trial_description = ""
            trial_path = ""
            remote = RemoteControl()
            res = remote.start_connection()

            command = 2
            prev_COP_r, prev_COP_l = 0, 0
            prev_frznorm, prev_flznorm = 0, 0
            copR, copL = 0, 0

            print("\nPress OK in Bertec Software!\n")

            print("\nTrial name: ", trial_name)

            Jetson = StreamJetson("172.24.44.177", 11)
            server_thread = threading.Thread(target=Jetson.start_server, daemon=True)
            server_thread.start()
            print("Jetson server started in a separate thread.")

            # Wait for Jetson to connect
            print("Waiting for Jetson to connect...")
            while not Jetson.connection:
                sleep(0.1)  # Wait for the Jetson to establish a connection
            print("Jetson connected successfully.")

            # Prompt for port number after Jetson connection
            port_number = int(input("Input Port number: "))

            rand_id = random.randint(0, 2**32 - 1)
            Nexus_notifier = CaptureNotifier(
                name=trial_name, notes=trial_notes, description=trial_description,
                database_path=trial_path, delay_ms=0, packet_id=rand_id, port=port_number
            )

            # sleep(15)
            params = {
                'leftVel': '0', 'leftAccel': '0.5', 'leftDecel': '0.5',
                'rightVel': '0', 'rightAccel': '0.5', 'rightDecel': '0.5'
            }
            res = remote.run_treadmill(
                params['leftVel'], params['leftAccel'], params['leftDecel'],
                params['rightVel'], params['rightAccel'], params['rightDecel']
            )
            

            Nexus_notifier.notify()
            vicon_start_time = time.time()  # Record when Vicon starts recording

            
            # Send start logging signal to Jetson after Nexus is started
            if Jetson.client_socket:
                send_start_logging_signal(Jetson.client_socket)
            else:
                print("[ERROR] No Jetson client socket available for start logging signal")
            
            
            timer_flag = 0
            while command:
                if timer_flag == 0:
                    start_time_trial = time.time()
                    timer_flag = 1
                elapsed_time_trial = time.time() - start_time_trial
                if elapsed_time_trial >= 30:
                    print("Stopping trial after 30 seconds")
                    command = 0
                    break

                # Initialize the data stream
                HasFrame = False
                timeout = 50
                while not HasFrame:
                    #print('.')
                    try:
                        if client.GetFrame():
                            HasFrame = True
                        timeout -= 1
                        if timeout < 0:
                            print('Failed to get frame')
                            sys.exit()
                    except ViconDataStream.DataStreamException as e:
                        client.GetFrame()
                client.SetStreamMode( ViconDataStream.Client.StreamMode.EServerPush )
                current_global_frame = client.GetFrameNumber()

                # Process devices to get Cy values for Right and Left
                copR, copL = 0, 0
                devices = client.GetDeviceNames()
                for deviceName, deviceType in devices:
                    deviceOutputDetails = client.GetDeviceOutputDetails(deviceName)
                    for outputName, componentName, unit in deviceOutputDetails:
                        if componentName == "Cy":
                            values, occluded = client.GetDeviceOutputValues(deviceName, outputName, componentName)
                            if deviceName == "Right":
                                copR = np.abs(values[0])  # if values else 0
                            elif deviceName == "Left":
                                copL = np.abs(values[0])  # if values else 0
                #Process to get grf values for Right and Left
                Flz,Frz,Flznorm,Frznorm = 0, 0,0,0
                forceplates = client.GetForcePlates()
                for plate in forceplates:
                    globalForceVectorData = client.GetGlobalForceVector(plate)
                    if plate == 1:
                        Frz = abs(globalForceVectorData[0][2])
                        Frznorm = Frz/(bw*10) # Normalize by body weight
                        GRFr.append(Frznorm)
                    if plate == 2:
                        Flz = abs(globalForceVectorData[0][2])
                        Flznorm = Flz/(bw*10) # Normalize by body weight
                        GRFl.append(Flznorm)

                if gc_countR <=1:
                    avg_time_gcR = 0
                    percent_gcR = 0
                else:
                    if avg_time_gcR > 0:
                        percent_gcR = (time.time()-time_hsR)/avg_time_gcR
                    else:
                        percent_gcR = 0
                    
                if gc_countL <=1:
                    avg_time_gcL = 0
                    percent_gcL = 0
                else:
                    if avg_time_gcL > 0:
                        percent_gcL = (time.time()-time_hsL)/avg_time_gcL
                    else:
                        percent_gcL = 0
                
                # Calculate phases first
                phaseR = determine_phase_grf_cop(Frznorm, prev_frznorm, copR, prev_COP_r,avg_time_gcR,percent_gcR)
                phaseL = determine_phase_grf_cop(Flznorm, prev_flznorm, copL, prev_COP_l,avg_time_gcL,percent_gcL)
                # print(phaseL, phaseR, percent_gcL, percent_gcR)

                
                try:
                    treadmill_data = { 
                        "vicon_timestamp": time.time(),
                        "copR": copR,
                        "copL": copL,
                        "Frznorm": Frznorm,
                        "Flznorm": Flznorm,}
                    treadmill_data_str = json.dumps(treadmill_data)  # Convert to string and ensure newline for parsing
                    Jetson.send_data(treadmill_data_str)  # Use the new send_data method
                    print(f"[DATA SENT] {treadmill_data_str}")
                except Exception as e:
                    print(f"[ERROR] Failed to send data: {e}")
                    break

                # Update previous COP values AFTER determining the phases
                prev_COP_r, prev_COP_l = copR, copL
                prev_frznorm, prev_flznorm = Frznorm, Flznorm
            
                       
                # Update gait cycle counters AFTER all percentage calculations and trigger checks
                if phaseR == 2:
                    if gc_countR == 0:
                        gc_countR += 1
                        time_hsR = time.time()
                    elif gc_countR>=1:
                        gc_countR += 1
                        prev_time_hsR = time_hsR
                        time_hsR = time.time()
                        if pert_flag == 0:
                            time_gcR.append(time_hsR - prev_time_hsR)
                            avg_time_gcR = np.mean(time_gcR)
                        #print(gc_countR)
                            

                if phaseL == 2:
                    if gc_countL == 0:
                        gc_countL += 1
                        time_hsL = time.time()
                    elif gc_countL>=1:
                        gc_countL += 1
                        prev_time_hsL = time_hsL
                        time_hsL = time.time()
                        if pert_flag ==0:
                            time_gcL.append(time_hsL - prev_time_hsL)
                            avg_time_gcL = np.mean(time_gcL)

                    
             
            params = {
                    'leftVel': '0',                'leftAccel': '0.5',                'leftDecel': '0.5',
                    'rightVel': '0',               'rightAccel': '0.5',               'rightDecel': '0.5'}
            res = remote.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])  

            rand_id = random.randint(0, 2**32 - 1)  #generate a Random unsigned integer
            Nexus = CaptureNotifier(name = trial_name, notes = trial_notes, description = trial_description, database_path = trial_path,
            delay_ms = 0, packet_id = rand_id, port = port_number)

            # Nexus.stop_capture()
            Nexus_notifier.close_socket()

            if Jetson.client_socket:
                Jetson.connection = False
                Jetson.client_socket.close()
                print("Jetson server closed.")

            print("Trial finished. Exiting experiment.")
            break
except ViconDataStream.DataStreamException as e:
    print( 'Handled data stream error', e )

if __name__ == "__main__":
    main()
