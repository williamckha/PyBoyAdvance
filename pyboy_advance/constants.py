from enum import IntFlag, IntEnum


class Interrupt(IntFlag):
    # fmt: off
    VBLANK      = 1 << 0
    HBLANK      = 1 << 1
    VCOUNT      = 1 << 2
    TIMER_0     = 1 << 3
    TIMER_1     = 1 << 4
    TIMER_2     = 1 << 5
    TIMER_3     = 1 << 6
    SERIAL      = 1 << 7
    DMA_0       = 1 << 8
    DMA_1       = 1 << 9
    DMA_2       = 1 << 10
    DMA_3       = 1 << 11
    KEYPAD      = 1 << 12
    GAMEPAK     = 1 << 13
    ALL         = 0x3FFF
    # fmt: on


class PowerDownMode(IntEnum):
    NONE = 0
    HALT = 1
    STOP = 2


class EventTrigger(IntEnum):
    TRIG_IMMEDIATELY = 0
    TRIG_VBLANK = 1
    TRIG_HBLANK = 2


class Key(IntFlag):
    # fmt: off
    BUTTON_A        = 1 << 0
    BUTTON_B        = 1 << 1
    BUTTON_SELECT   = 1 << 2
    BUTTON_START    = 1 << 3
    DPAD_RIGHT      = 1 << 4
    DPAD_LEFT       = 1 << 5
    DPAD_UP         = 1 << 6
    DPAD_DOWN       = 1 << 7
    SHOULDER_RIGHT  = 1 << 8
    SHOULDER_LEFT   = 1 << 9
    # fmt: on
