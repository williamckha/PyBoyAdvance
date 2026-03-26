from enum import IntEnum


class WindowEvent(IntEnum):
    # fmt: off
    NONE                    = 1

    QUIT                    = 2
    FULLSCREEN              = 3

    PRESS_BUTTON_A          = 4
    PRESS_BUTTON_B          = 5
    PRESS_BUTTON_SELECT     = 6
    PRESS_BUTTON_START      = 7
    PRESS_DPAD_RIGHT        = 8
    PRESS_DPAD_LEFT         = 9
    PRESS_DPAD_UP           = 10
    PRESS_DPAD_DOWN         = 11
    PRESS_SHOULDER_RIGHT    = 12
    PRESS_SHOULDER_LEFT     = 13

    RELEASE_BUTTON_A        = 14
    RELEASE_BUTTON_B        = 15
    RELEASE_BUTTON_SELECT   = 16
    RELEASE_BUTTON_START    = 17
    RELEASE_DPAD_RIGHT      = 18
    RELEASE_DPAD_LEFT       = 19
    RELEASE_DPAD_UP         = 20
    RELEASE_DPAD_DOWN       = 21
    RELEASE_SHOULDER_RIGHT  = 22
    RELEASE_SHOULDER_LEFT   = 23
    # fmt: on
