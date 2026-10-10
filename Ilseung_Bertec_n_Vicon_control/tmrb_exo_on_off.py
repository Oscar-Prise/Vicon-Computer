# Drafted by Changseob Song, 11/1/2024
# This is an example code to trigger starts of Vicon Nexus and Bertec FIT5

from Header_BertecControl import BertecController
from Header_NexusControl import NexusController
from Header_JetsonControl import JetsonController
import numpy as np
from time import sleep
import random
import time

def main():  
    subject_name = "Ilseung_sensor_off"
    task_name = "LG"
    condition_name = "exo_on"

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
        trial_name = subject_name + "-" + task_name + '-' + condition_name + '-' + str(trial_number)
        print("\nTrial name: ", trial_name)

        # Connect Jetson
        if use_exo:
            Jetson = JetsonController("172.24.44.177", 10)
            Jetson.start_server()

        # Create Nexus instance
        packet_id= random.randint(0, 2**32 - 1) 
        Nexus = NexusController(name= trial_name, notes = trial_notes, description = trial_description, database_path = " ",
        delay_ms = 0, packet_id = packet_id, port = 1)
        
        command = input("Input protocol number (exit for 0):")


        speeds = np.array([1.2])
        print(speeds)
        # speeds = np.linspace(0.4,3.5,1000)
        # speeds = np.array([1.2])
        # sleep(20)
        if (command == '1'):
            
            speed_1 = 1.25

            if 'RD' in task_name: speeds *= -1

            Nexus.notify()
            # sleep(2)
            if use_exo:
                Jetson.send_message("exo on")
            for i in range(len(speeds)):
                print(f"\nTreadmill speed: {speeds[i]} m/s")
                params = {
                    'leftVel': str(speeds[i]),                'leftAccel': '1',                'leftDecel': '1',
                    'rightVel': str(speeds[i]),               'rightAccel': '1',               'rightDecel': '1'}
                res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
                sleep(60)
                                    

            # 2. Stop Treadmill
            print("\nTreadmill stop")
            params = {
                'leftVel': '0',                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': '0',               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
    

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