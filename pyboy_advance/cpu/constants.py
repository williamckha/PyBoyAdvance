from enum import IntEnum


class CPUState(IntEnum):
    ARM = 0
    THUMB = 1


class CPUMode(IntEnum):
    USER = 0b10000
    FIQ = 0b10001
    IRQ = 0b10010
    SWI = 0b10011
    ABORT = 0b10111
    UNDEFINED = 0b11011
    SYSTEM = 0b11111


class Condition(IntEnum):
    EQ = 0x0
    NE = 0x1
    HS = 0x2
    LO = 0x3
    MI = 0x4
    PL = 0x5
    VS = 0x6
    VC = 0x7
    HI = 0x8
    LS = 0x9
    GE = 0xA
    LT = 0xB
    GT = 0xC
    LE = 0xD
    AL = 0xE
    NV = 0xF


class ShiftType(IntEnum):
    LSL = 0
    LSR = 1
    ASR = 2
    ROR = 3


class ExceptionVector(IntEnum):
    EV_RESET = 0x00
    EV_UNDEFINED_INSTRUCTION = 0x04
    EV_SWI = 0x08
    EV_PREFETCH_ABORT = 0x0C
    EV_DATA_ABORT = 0x10
    EV_ADDRESS_EXCEEDS_26_BITS = 0x14
    EV_IRQ = 0x18
    EV_FIQ = 0x1C


class BankIndex(IntEnum):
    BANK_SYSTEM_USER = 0
    BANK_FIQ = 1
    BANK_IRQ = 2
    BANK_SWI = 3
    BANK_ABORT = 4
    BANK_UNDEFINED = 5


ARM_PC_INCREMENT = 4
THUMB_PC_INCREMENT = 2
