#Maria 5/1/2025#Using grf and cop 
from vicon_dssdk import ViconDataStream
from Header_NexusControl import CaptureNotifier
from Header_BertecControl import RemoteControl
import argparse
import sys
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import random
import csv
import time
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('host', nargs='?', help="Host name, in the format of server:port", default = "localhost:801")
args = parser.parse_args()
global  GRFl, GRFr, Frz, Frl, getted_frames, time_step, phases, copR, copL, prev_COP_r, prev_COP_l, phaseR, phaseL, pert_flag, copL_list, copR_list, pert_frames, pert_reasons, gc_count, current_global_frame, Flz, Flr, Flznorm, Frznorm, phaseL_list, phaseR_list
client = ViconDataStream.Client()
pert_flag = 0
GRFr = []
GRFl = []
phases = []
getted_frames = []
pert_frames = []
pert_flag = 0
pert_reasons = []
gc_countR = 0
gc_countL = 0
copL_list = []
copR_list = []
phaseR_list = []
phaseL_list = []
time_gcR = []
time_gcL = []
avg_time_gcR = 0
avg_time_gcL = 0
percent_gcR = 0
percent_gcL = 0
# At the end of the main function, save the combined data

from time import sleep
import time

import csv

def save_to_csv_combined(frames, copR_list, copL_list, grfr, grfl, phaseR_list, phaseL_list, filename):
    """Save COP and gait phases to a CSV file."""
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Add headers
        writer.writerow(["Frame","COP_Right", "COP_Left", "GRF_Right", "GRF_Left", "Gait_Phase_Right", "Gait_Phase_Left"])
        # Write rows combining all lists
        for frame, copR, copL,  grfl, grfr , phaseR, phaseL in zip(frames, copR_list, copL_list, grfr, grfl , phaseR_list, phaseL_list):
            writer.writerow([frame, copR, copL, grfr, grfl, phaseR, phaseL])

    
def determine_phase_grf_cop(Fznorm, prev_fznorm,cop, prev_cop,avg_time_gc,percent_gc):
    """Helper function to determine the phase for a given side."""

    if cop > 0 and prev_cop == 0:
        return 2 #heel strike
    
    elif avg_time_gc !=0 and prev_cop >0 and cop == 0:
        return 3  # toe-off
        
    elif cop> 0 and prev_cop > 0:
        return 1 #stance
    else:
        return 0 #swing

try:
    client.Connect( args.host )
    client.SetBufferSize( 1 ) 
    client.EnableDeviceData()
    

    def main():
        trial_number = 0
    
        global gc_countR,gc_countL, pert_flag, current_global_frame, pert_frames, pert_reasons, bw, time_hsR, time_gcR, prev_time_hsR, time_hsL, time_gcL, prev_time_hsL

        bw = 61   # Body weight in (kg)
        #stop_condition = random.choice(["lhs", "rto", "lto","rhs"]) #move to top
        stop_condition = 'rto'
        speed = "test"
        trial_name = f"{stop_condition.upper()}_{speed}_"
        trial_notes = ""
        trial_description = ""
        trial_path = ""
        remote = RemoteControl()
        res = remote.start_connection()

        command = 1
        prev_COP_r, prev_COP_l = 0, 0
        prev_frznorm, prev_flznorm = 0, 0
        copR, copL = 0, 0

        print("\nPress OK in Bertec Software!\n")
        trial_number = 20
        trial_name = trial_name + str(trial_number)
        print("\nTrial name: ", trial_name)

        # Jetson = JetsonController("172.24.44.177", 10)
        # Jetson.start_server()

        port_number = int(input("Input Port number:"))
        rand_id = random.randint(0, 2**32 - 1)
        Nexus_notifier = CaptureNotifier(
            name=trial_name, notes=trial_notes, description=trial_description,
            database_path=trial_path, delay_ms=0, packet_id=rand_id, port=port_number
        )

    #add lines so it doesnt promport for port number untill jetson connected 

        sleep(10)
        params = {
            'leftVel': '0.0', 'leftAccel': '0.5', 'leftDecel': '0.5',
            'rightVel': '0.0', 'rightAccel': '0.5', 'rightDecel': '0.5'
        }
        remote.run_treadmill(
            params['leftVel'], params['leftAccel'], params['leftDecel'],
            params['rightVel'], params['rightAccel'], params['rightDecel']
        )
        
        
    
        # Jetson.send_message("exo on")

        Nexus_notifier.notify()

        start_time_trial = time.time()
        while command:
            elapsed_time_trial = time.time() - start_time_trial
            if elapsed_time_trial >= 20:
                print("Stopping trial after 15 seconds")
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
            getted_frames.append(current_global_frame)

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
                    # print(GRFr)
                    #print(Frznorm)
                if plate == 2:
                    Flz = abs(globalForceVectorData[0][2])
                    Flznorm = Flz/(bw*10) # Normalize by body weight
                    GRFl.append(Flznorm)
                    # print(Flz)
                    #print(Flznorm)
            # print(Frz,Flz)

            copL_list.append(copL)
            copR_list.append(copR)
            # print(copR)
            if gc_countR <=1:
                avg_time_gcR = 0
                percent_gcR = 0
            else:
                percent_gcR = (time.time()-time_hsR)/avg_time_gcR

            if gc_countL <=1:
                avg_time_gcL = 0
                percent_gcL = 0
            else:
                percent_gcL = (time.time()-time_hsL)/avg_time_gcL
            
            # print(percent_gcR)
            phaseR = determine_phase_grf_cop(Frznorm, prev_frznorm, copR, prev_COP_r,avg_time_gcR,percent_gcR)
            phaseL = determine_phase_grf_cop(Flznorm, prev_flznorm, copL, prev_COP_l,avg_time_gcL,percent_gcL)
            #print("got phase:",time.time()-start_time_trial)
            if phaseR == 2:
                if gc_countR == 0:
                    gc_countR += 1
                    time_hsR = time.time()
                elif gc_countR>=1:
                    gc_countR += 1
                    print("gc_countR:",gc_countR)
                    prev_time_hsR = time_hsR
                    time_hsR = time.time()
                    if pert_flag == 0:
                        time_gcR.append(time_hsR - prev_time_hsR)
                        avg_time_gcR = np.mean(time_gcR)
            
            # print(gc_countR)


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

            
            # Update previous COP values AFTER determining the phases
            prev_COP_r, prev_COP_l = copR, copL
            prev_frznorm, prev_flznorm = Frznorm, Flznorm

            # Stop treadmill based on specific phases
            #pert_random_onset = random.randint(6, 8)
            pert_random_onset = 4
            #if gc_countR> pert_random_onset-1 and pert_flag == 0:
                #stop_condition = random.choice(["lhs", "rto", "lto","rhs"]) #move to top
                #stop_condition = "rto" #move to top
            # if gc_countR > pert_random_onset and pert_flag == 0:
            #     if stop_condition == "rhs" and phaseR == 2:
            #         time_intopert = time.time() - start_time_trial
            #         print("Perturbation started at:", time_intopert)
            #         #slip_treadmill_right_hs(remote,start_time_trial)
            #         pert_flag = 1
            #         print(stop_condition)
                    
            #     elif stop_condition == "lhs" and phaseL == 2:
            #         #time_intopert = time.time()
            #         #slip_treadmill_left_hs(remote,start_time_trial)
            #         time_intopert = time.time() - start_time_trial
            #         print("Perturbation started at:", time_intopert)
            #         pert_flag = 1
            #         print(stop_condition)

            #     elif stop_condition == "rto" and phaseR ==3:
            #         time_intopert = time.time() - start_time_trial
            #         print("Perturbation started at:", time_intopert)
            #         #time_intopert = time.time()
            #         #slip_treadmill_right_to(remote,start_time_trial)
            #         pert_flag = 1
            #         #print(stop_condition)

            #     elif stop_condition == "lto" and phaseL == 3:
            #         time_intopert = time.time() - start_time_trial
            #         print("Perturbation started at:", time_intopert)
            #         #time_intopert = time.time()
            #         #slip_treadmill_left_to(remote,start_time_trial)
            #         pert_flag = 1
            #         print(stop_condition)

            #         # print(current_global_frame-pert_frames[0])
            # else: 
            #     pert_frames.append(current_global_frame)  # Append empty value for non-perturbation frames
            #     pert_reasons.append("none")  # Append empty value for non-perturbation reasons
            #print(gc_count)
            phaseR_list.append(phaseR)
            phaseL_list.append(phaseL)
            pert_frames.append(current_global_frame)  # Append empty value for non-perturbation frames
            print(phaseR)
                
#stoptreadmill
        # Jetson.send_message("exo off")
        params = {
                'leftVel': '0',                'leftAccel': '0.5',                'leftDecel': '0.5',
                'rightVel': '0',               'rightAccel': '0.5',               'rightDecel': '0.5'}
        res = remote.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])  
        # Save data to CSV
        pert_frames = [frame - pert_frames[0] for frame in pert_frames]

        # save_to_csv_combined(pert_frames,copR_list, copL_list,GRFl,GRFr,  phaseR_list, phaseL_list, "testtststcsv")

        
        rand_id = random.randint(0, 2**32 - 1)  #generate a Random unsigned integer
        Nexus = CaptureNotifier(name = trial_name, notes = trial_notes, description = trial_description, database_path = trial_path,
        delay_ms = 0, packet_id = rand_id, port = port_number)
        #print(time_intopert-start_time_trial)
        Nexus.stop_capture()
        Nexus_notifier.close_socket()
except ViconDataStream.DataStreamException as e:
    print( 'Handled data stream error', e )

if __name__ == "__main__":
    main()
