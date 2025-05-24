from enum import Enum


class CPUState(Enum):
    ARM = 0
    THUMB = 1


class CPUMode(Enum):
    USER = 0b10000
    FIQ = 0b10001
    IRQ = 0b10010
    SWI = 0b10011
    ABORT = 0b10111
    UNDEFINED = 0b11011
    SYSTEM = 0b11111
