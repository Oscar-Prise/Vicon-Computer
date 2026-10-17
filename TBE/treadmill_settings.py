# Treadmill settings (speed profiles) for main_TBE.py
#
# Each setting is a list of segments that run in order. A segment holds a speed
# for `duration` seconds (the timer starts as soon as the command is sent, so
# the ramp to the new speed counts toward the duration). The trial length is the
# sum of all segment durations; after the last one the treadmill is stopped with
# STOP_DECEL.
#
# Segment keys:
#   speed     : belt speed in m/s (both belts). Negative = backwards.
#   duration  : how long to hold this segment, in seconds
#   accel     : (optional) m/s^2 used to speed up,  default DEFAULT_ACCEL
#   decel     : (optional) m/s^2 used to slow down, default DEFAULT_DECEL
#   left/right: (optional) per-belt speeds in m/s for split-belt; overrides `speed`

DEFAULT_ACCEL = 0.5
DEFAULT_DECEL = 0.5
STOP_DECEL = 0.5

SETTINGS = {
    # LG_1p2_ExoOn: continuous 45 s at 1.2 m/s, then stop
    "default": [
        {"speed": 1.2, "duration": 45},
    ],

    # Example for later:
    # "steps": [
    #     {"speed": 0.8, "duration": 30},
    #     {"speed": 1.2, "duration": 30},
    # ],
}
