# Drafted by Changseob Song, 11/1/2024
# This is an example code to trigger starts of Vicon Nexus and Bertec FIT5

from Header_BertecControl import BertecController
from Header_NexusControl import NexusController
from time import sleep
import time

def main():  

    subject_name = "AB11_Cole"
    condition_name = "exoon_1p0mps"
    trial_name = subject_name + "_" + condition_name

    trial_notes = "241117 Run by master python script."
    trial_description = (" ")
    trial_path = "D:/Jeremy/Susan/Captures/Take"

    # Create an instance of BertecControl
    Bertec = BertecController()
    res = Bertec.start_connection()
    # print(res)
    command = 1
    res = ' '
    trial_number = 0

    print("\nPress OK in Bertec Software!\n")

    while(command):
        
        trial_number += 1
        print("\nTrial number: ", trial_number)
        trial_name = trial_name + str(trial_number)
        print("\nTrial name: ", trial_name)

        # Port number should match with the port number in Nexus
        # !!!! Port number need to be different from previous trial every time running this code. (EX. you can do 30 -> 31 -> 30 -> 31 ...)
        port_number = int(input("Input Port number:"))

        # Create an instance of NexusController
        Nexus = NexusController(name = trial_name, notes = trial_notes, description = trial_description, database_path = trial_path,
        delay_ms = 0, packet_id = 33360, port = port_number)
        
        command = input("Input protocol number (exit for 0):")

        if (command == '1'):

            t_0 = time.time()

            # Trigger Nexus Capture
            Nexus.notify()
            
            sleep(2.5)

            t_1 = time.time()
            print(t_1 - t_0)

            # 
            print("\nTreadmill speed: 1.1 m/s")
            params = {
                'leftVel': '1.1',                'leftAccel': '0.5',                'leftDecel': '0.5',
                'rightVel': '1.1',               'rightAccel': '0.5',               'rightDecel': '0.5'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            sleep(45)

            t_2 = time.time()
            print(t_2 - t_0)

            print("\nTreadmill speed: 0.5 m/s")
            params = {
                'leftVel': '0.5',                'leftAccel': '0.5',                'leftDecel': '0.5',
                'rightVel': '0.5',               'rightAccel': '0.5',               'rightDecel': '0.5'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            sleep(45)

            t_3 = time.time()
            print(t_3 - t_0)

            print("\nTreadmill speed: 1.2 m/s")
            params = {
                'leftVel': '1.2',                'leftAccel': '0.5',                'leftDecel': '0.5',
                'rightVel': '1.2',               'rightAccel': '0.5',               'rightDecel': '0.5'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            sleep(45)

            t_4 = time.time()
            print(t_4 - t_0)            

            print("\nTreadmill speed: 0.6 m/s")
            params = {
                'leftVel': '0.6',                'leftAccel': '0.5',                'leftDecel': '0.5',
                'rightVel': '0.6',               'rightAccel': '0.5',               'rightDecel': '0.5'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            sleep(45)

            t_5 = time.time()
            print(t_5 - t_0)  

            print("\nTreadmill speed: 0 m/s")
            params = {
                'leftVel': '0.0',                'leftAccel': '0.5',                'leftDecel': '0.5',
                'rightVel': '0.0',               'rightAccel': '0.5',               'rightDecel': '0.5'}
            res = Bertec.run_treadmill(params['leftVel'], params['leftAccel'], params['leftDecel'], params['rightVel'], params['rightAccel'], params['rightDecel'])

            sleep(2.5)

            t_6 = time.time()
            print(t_6 - t_0)  

        
        elif (command == '2'):
            print("Using run_treadmill")
            params = {
                'leftVel': '0',                'leftAccel': '1',                'leftDecel': '1',
                'rightVel': '0',               'rightAccel': '1',               'rightDecel': '1'}
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