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
