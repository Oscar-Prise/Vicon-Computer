# Run the Bertec treadmill and/or record the trial in Vicon Nexus
#
# Flow: connect Bertec (if TREADMILL_ON) -> enter Nexus port (if VICON_REC) -> Enter -> countdown
#       -> treadmill starts (if TREADMILL_ON) + Vicon capture starts (if VICON_REC)
#       -> trial runs for TRIAL_TIME_S -> treadmill stops + Vicon capture stops (saved as TRIAL_NAME)
#
# Usage: edit the parameters below, then run
#   python main_treadmill.py
#
# Nexus: enable the UDP remote trigger and set the same port number entered here.

# ===================== Changeable parameters =====================
TREADMILL_ON = True         # True: run the treadmill. False: belts stay still (SPEED/ACCEL/DECEL ignored)
VICON_REC = True            # True: record in Vicon Nexus. False: no Nexus recording
TRIAL_NAME = "NoExo_LG_1p2" # Vicon trial name
NEXUS_PORT = None           # Nexus UDP trigger port; None = ask at runtime

START_DELAY_S = 10          # countdown before the trial starts (s)
TRIAL_TIME_S = 30           # trial length (s), treadmill ramp-up included

SPEED = 1.2                 # belt speed (m/s), both belts. Negative = backwards
ACCEL = 0.5                 # acceleration used to speed up (m/s^2)
DECEL = 0.5                 # deceleration used to stop at the end (m/s^2)
# =================================================================

from Header_BertecControl import BertecController
from Header_NexusControl import CaptureNotifier
import random
import time


def set_treadmill(Bertec, left_vel, right_vel, accel, decel):
    """Send a one-shot Bertec speed command."""
    return Bertec.run_treadmill(str(left_vel), str(accel), str(decel),
                                str(right_vel), str(accel), str(decel))


def stop_treadmill(Bertec):
    print("\nTreadmill stop", flush=True)
    set_treadmill(Bertec, 0, 0, ACCEL, DECEL)


def main():
    if not TREADMILL_ON and not VICON_REC:
        print("TREADMILL_ON and VICON_REC are both False, nothing to do.")
        return

    # With the treadmill off we never connect to Bertec, so no speed command can be sent
    Bertec = None
    if TREADMILL_ON:
        Bertec = BertecController()
        res = Bertec.start_connection()
        if res is None:
            print("Could not connect to Bertec. Is the Bertec software open with remote control enabled?")
            return
        print(f"\nTreadmill: {SPEED} m/s for {TRIAL_TIME_S}s (accel {ACCEL}, decel {DECEL} m/s^2)")
    else:
        print(f"\nTreadmill: OFF (belts stay still), trial length {TRIAL_TIME_S}s")
    print(f"Vicon recording: {'ON, trial name ' + TRIAL_NAME if VICON_REC else 'OFF'}")
    if TREADMILL_ON:
        print("\nPress OK in Bertec Software if prompted!")

    Nexus_notifier = None
    recording = False
    try:
        if VICON_REC:
            # Port number must match the one in Nexus (use a new port if Nexus ignores a repeated trigger)
            port_number = NEXUS_PORT if NEXUS_PORT is not None else int(input("Input Nexus port number: "))
            Nexus_notifier = CaptureNotifier(
                name=TRIAL_NAME, notes="", description="", database_path="",
                delay_ms=0, packet_id=random.randint(0, 2**32 - 1), port=port_number
            )

        input(f"\nPress Enter to start the {START_DELAY_S}s countdown...")
        for remaining in range(START_DELAY_S, 0, -1):
            print(f"  {remaining}...", flush=True)
            time.sleep(1)
        print("Starting trial now.\n", flush=True)

        if VICON_REC:
            Nexus_notifier.notify()  # start Vicon recording
            recording = True
        if TREADMILL_ON:
            set_treadmill(Bertec, SPEED, SPEED, ACCEL, DECEL)
        time.sleep(TRIAL_TIME_S)
        print(f"Trial finished after {TRIAL_TIME_S}s.", flush=True)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Always stop the belts and the Vicon capture, even on Ctrl+C or an error
        if Bertec is not None:
            stop_treadmill(Bertec)
        if recording:
            Nexus_notifier.stop_capture()
        if Bertec is not None:
            Bertec.stop_connection()
        print("Done.")


if __name__ == "__main__":
    main()
