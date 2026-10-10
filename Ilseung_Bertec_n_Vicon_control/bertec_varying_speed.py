# Modified by Changseob Song (Updated for a repetitive 6-minute linear triangle wave profile: 3s ramp up, 3s ramp down)
# This is an example code to trigger starts of Vicon Nexus and Bertec FIT5

from Header_BertecControl import BertecController
from Header_NexusControl import NexusController
from Header_JetsonControl import JetsonController
import numpy as np
from time import sleep
import random
import time

def main(): 
    subject_name = "Itak"
    task_name = "RA"
    condition_name = "no_exo"

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
        packet_id = random.randint(0, 2**32 - 1) 
        Nexus = NexusController(name=trial_name, notes=trial_notes, description=trial_description, database_path=" ",
        delay_ms=0, packet_id=packet_id, port=1)
        
        command = input("Input protocol number (exit for 0):")

        if (command == '1'):
            if 'RD' in task_name: 
                multiplier = -1
            else: 
                multiplier = 1

            Nexus.notify()
            if use_exo:
                Jetson.send_message("exo on")

            # **Repetitive Linear Triangle Wave Parameters**
            min_speed = 0.5 * multiplier
            max_speed = 1.0 * multiplier
            ramp_time = 5.0  # 3 seconds for each ramp (up and down)
            delta_speed = 0.5  # 1.0 - 0.5
            ramp_rate = str(round(delta_speed / ramp_time, 6))

            total_duration_sec = 6 * 60  # 6 minutes = 360 seconds
            cycle_duration = ramp_time * 2  # 6 seconds per full cycle (3s up + 3s down)
            num_cycles = int(total_duration_sec / cycle_duration)  # 60 cycles total

            print(f"\nStarting 6-minute repetitive linear triangle profile ({num_cycles} cycles, 3s up / 3s down).")

            # 1. Initial baseline speed (start at min speed: 0.5)
            print(f"\nSetting initial speed: {min_speed} m/s")
            params = {
                'leftVel': str(min_speed),   'leftAccel': '0.5',   'leftDecel': '0.5',
                'rightVel': str(min_speed),  'rightAccel': '0.5',  'rightDecel': '0.5'}
            Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(2.0)

            # 2. Run repetitive triangle cycles until 6 minutes are reached
            for cycle in range(num_cycles):
                print(f"\nCycle {cycle + 1}/{num_cycles}")

                # Ramp Up: 0.5 -> 1.0 over 3 seconds
                params = {
                    'leftVel': str(max_speed),   'leftAccel': ramp_rate,   'leftDecel': ramp_rate,
                    'rightVel': str(max_speed),  'rightAccel': ramp_rate,  'rightDecel': ramp_rate}
                Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
                sleep(ramp_time)

                # Ramp Down: 1.2 -> 0.5 over 3 seconds
                params = {
                    'leftVel': str(min_speed),   'leftAccel': ramp_rate,   'leftDecel': ramp_rate,
                    'rightVel': str(min_speed),  'rightAccel': ramp_rate,  'rightDecel': ramp_rate}
                Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
                sleep(ramp_time)

            # 3. Stop Treadmill
            print("\nTreadmill stop")
            params = {
                'leftVel': '0',               'leftAccel': '0.5',               'leftDecel': '0.2',
                'rightVel': '0',              'rightAccel': '0.5',              'rightDecel': '0.2'}
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