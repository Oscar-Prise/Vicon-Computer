# Treadmill settings (speed profiles) for main_treadmill.py
#
# Each setting is a list of segments that run in order. A segment holds a speed
# for `duration` seconds (the timer starts as soon as the command is sent, so
# the ramp to the new speed counts toward the duration).
#
# Segment keys:
#   speed     : belt speed in m/s (both belts). Negative = backwards.
#   duration  : how long to hold this segment, in seconds
#   accel     : (optional) m/s^2 used to speed up,  default DEFAULT_ACCEL
#   decel     : (optional) m/s^2 used to slow down, default DEFAULT_DECEL
#   left/right: (optional) per-belt speeds in m/s for split-belt; overrides `speed`
#
# After the last segment the treadmill is stopped with STOP_DECEL.
#
# To add a new setting, add a new entry to SETTINGS and run:
#   python main_treadmill.py <setting_name>

DEFAULT_ACCEL = 0.5
DEFAULT_DECEL = 0.5
STOP_DECEL = 0.5

SETTINGS = {
    # 1.2 m/s for 1 minute straight, then stop
    "default": [
        {"speed": 1.2, "duration": 60},
    ],

    # Examples for later (uncomment / edit as needed):
    # "steps": [
    #     {"speed": 0.8, "duration": 30},
    #     {"speed": 1.2, "duration": 30},
    #     {"speed": 1.6, "duration": 30},
    # ],
    # "split_belt": [
    #     {"left": 1.0, "right": 1.4, "duration": 60},
    # ],
}
