# Drafted by Changseob Song, 11/1/2024
# This is an example code to trigger starts of Vicon Nexus and Bertec FIT5

from Header_BertecControl import BertecController
from Header_NexusControl import NexusController
from Header_NexusControl2 import CaptureNotifier
from Header_JetsonControl import JetsonController
import numpy as np
from time import sleep
import random
import time

def main():  
    subject_name = "ab01_jimin"
    task_name = "sq"
    condition_name = "exo_on"
    # condition_name = "no_exo"

    # trial_start_sec = 10
    # trial_duration_sec = 20

    trial_notes = " "
    trial_description = " "

    if "no_exo" in condition_name: use_exo = False
    elif "exo_off" in condition_name: use_exo = False
    else: use_exo = True
    
    # Create an instance of BertecControl
    Bertec = BertecController()
    res = Bertec.start_connection()
    command = 1
    trial_number = 0

    while(command):
        
        trial_number += 1
        trial_name = subject_name + "_" + task_name + '_' + condition_name + '_' + str(trial_number)
        print("\nTrial name: ", trial_name)

        # Connect Jetson
        if use_exo:
            Jetson = JetsonController("172.24.44.177", 10)
            Jetson.start_server()

        # Create Nexus instance
        packet_id= random.randint(0, 2**32 - 1) 
        Nexus = CaptureNotifier(name= trial_name, notes = trial_notes, description = trial_description, database_path = " ",
        delay_ms = 0, packet_id = packet_id, port = 1)
        
        command = input("Input protocol number (exit for 0):")

        # speeds = np.array([0.8,1.4,1.6,1.8,2.0,2.2,1.8,2.0,2.2,2.4,2.6])
        # LG_speeds = np.array([0.8,1.2,1.6])

        '''
        Knee Exoskeleton Trial Conditions:
        1. LG: 1.2 m/s
        2. RA: 0.8 m/s
        3. RD: 0.8 m/s
        '''

        LG_speeds = np.array([1.2])
        speeds = LG_speeds

        # RARD_speeds = np.array([0.8])
        # speeds = RARD_speeds

        if (command == '1'):
            
            # speed_1 = 1.25

            if 'RD' in task_name: speeds *= -1

            Nexus.notify()
            # sleep(5)
            if use_exo:
                Jetson.send_message("exo on")
            for i in range(len(speeds)):
                print(f"\nTreadmill speed: {speeds[i]} m/s")
                params = {
                    'leftVel': str(speeds[i]),                'leftAccel': '0.5',                'leftDecel': '0.5',
                    'rightVel': str(speeds[i]),               'rightAccel': '0.5',               'rightDecel': '0.5'}
                # sleep(320)
                sleep(250)
                                    

            # 2. Stop Treadmill
            print("\nTreadmill stop")
            params = {
                'leftVel': '0',                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': '0',               'rightAccel': '0.5',               'rightDecel': '0.2'}
    

        elif (command == '6'):
            print("Using get_force_data")
            res = Bertec.get_force_data()
            
        elif (command == '0'):
            print("Exiting program")
            Bertec.stop_connection()
            command = 0


    Bertec.stop_connection()
    Nexus.close_socket()

if __name__ == "__main__":
    main()