# Drafted by Changseob Song, 11/1/2024
# This is an example code to trigger starts of Vicon Nexus and Bertec FIT5

from Header_BertecControl import BertecController
from Header_NexusControl import NexusController
from Header_JetsonControl import JetsonController
from time import sleep
import random
import time

def main():  
    subject_name = "AB03_Jinwoo"
    task_name = "LG"
    condition_name = "exo_on_simulation_torque_profile"

    trial_start_sec = 0
    trial_duration_sec = 165

    trial_notes = " "
    trial_description = " "

    if "no_exo" in condition_name: use_exo = False
    elif "exo_off" in condition_name: use_exo = False
    else: use_exo = False

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

        if (command == '1'):
            
            speed_1 = 1.2

            if 'RD' in task_name: speed_1 *= -1

            print(f"\nTreadmill speed: {speed_1} m/s")
            params = {
                'leftVel': str(speed_1),                'leftAccel': '0.5',                'leftDecel': '0.5',
                'rightVel': str(speed_1),               'rightAccel': '0.5',               'rightDecel': '0.5'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
                                    
            # 1. Trigger Jetson
            if use_exo:
                Jetson.send_message("exo on")

            sleep(trial_start_sec)

            # 2. Trigger Nexus Capture
            Nexus.notify()
            
            sleep(trial_duration_sec+5)

            # 2. Stop Treadmill
            print("\nTreadmill stop")
            params = {
                'leftVel': '0',                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': '0',               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
        
        elif (command == '2'):
            
            if 'RD' in condition_name:
                sign = -1
            else:
                sign = 1

            # 1. Trigger Jetson
            if use_exo:
                Jetson.send_message("exo on")

            # 2. Trigger Nexus Capture
            Nexus.notify()

            speed = 0.6 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            speed = 0.7 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            speed = 0.8 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            speed = 0.9 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            speed = 1.0 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            speed = 1.1 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            speed = 1.2 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])                    
            sleep(15)

            speed = 1.3 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            speed = 1.4 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])          
            sleep(15)

            speed = 1.5 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            speed = 1.6 * sign
            print(f"\nTreadmill speed: {speed} m/s")
            params = {
                'leftVel': str(speed),                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': str(speed),               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])
            sleep(15)

            sleep(5)

            # 2. Stop Treadmill
            print("\nTreadmill stop")
            params = {
                'leftVel': '0',                'leftAccel': '0.5',                'leftDecel': '0.2',
                'rightVel': '0',               'rightAccel': '0.5',               'rightDecel': '0.2'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

        elif (command == '3'):

            speed_1 = 1.5
            accel_1 = 0.2
            print(f"\nTreadmill speed: {speed_1} m/s")
            params = {
                'leftVel': str(speed_1),                'leftAccel': str(accel_1),                'leftDecel': str(accel_1),
                'rightVel': str(speed_1),               'rightAccel': str(accel_1),               'rightDecel': str(accel_1)}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            # 1. Trigger Jetson
            # Jetson.trigger_jetson("exo on")

            # 2. Trigger Nexus Capture
            Nexus.notify()
            
            sleep(7.5)

            # 1. Stop Jetson
            #Jetson.trigger_jetson("exo off")

            # 2. Stop Treadmill
            speed_2 = 0
            print(f"\nTreadmill speed: {speed_2} m/s")
            params = {
                'leftVel': str(speed_2),                'leftAccel': str(accel_1),                'leftDecel': str(accel_1),
                'rightVel': str(speed_2),               'rightAccel': str(accel_1),               'rightDecel': str(accel_1)}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            sleep(7.5)

        elif (command == '4'):

            speed_1 = 1.5
            accel_1 = 0.1
            print(f"\nTreadmill speed: {speed_1} m/s")
            params = {
                'leftVel': str(speed_1),                'leftAccel': str(accel_1),                'leftDecel': str(accel_1),
                'rightVel': str(speed_1),               'rightAccel': str(accel_1),               'rightDecel': str(accel_1)}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            # 1. Trigger Jetson
            Jetson.trigger_jetson("exo on")

            # 2. Trigger Nexus Capture
            Nexus.notify()
            
            sleep(15)

            #Jetson.trigger_jetson("exo off")


            # 2. Stop Treadmill
            speed_2 = 0
            print(f"\nTreadmill speed: {speed_2} m/s")
            params = {
                'leftVel': str(speed_2),                'leftAccel': str(accel_1),                'leftDecel': str(accel_1),
                'rightVel': str(speed_2),               'rightAccel':str(accel_1),               'rightDecel': str(accel_1)}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            sleep(15) 

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