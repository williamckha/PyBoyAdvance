# This file was auto-generated using `setup.py generate_constants_pyx`
# Generated from pyboy_advance/cpu/constants.py

cpdef enum CPUState:
    ARM = 0
    THUMB = 1

cpdef enum CPUMode:
    USER = 16
    FIQ = 17
    IRQ = 18
    SWI = 19
    ABORT = 23
    UNDEFINED = 27
    SYSTEM = 31

cpdef enum Condition:
    EQ = 0
    NE = 1
    HS = 2
    LO = 3
    MI = 4
    PL = 5
    VS = 6
    VC = 7
    HI = 8
    LS = 9
    GE = 10
    LT = 11
    GT = 12
    LE = 13
    AL = 14
    NV = 15

cpdef enum ShiftType:
    LSL = 0
    LSR = 1
    ASR = 2
    ROR = 3

cpdef enum ExceptionVector:
    EV_RESET = 0
    EV_UNDEFINED_INSTRUCTION = 4
    EV_SWI = 8
    EV_PREFETCH_ABORT = 12
    EV_DATA_ABORT = 16
    EV_ADDRESS_EXCEEDS_26_BITS = 20
    EV_IRQ = 24
    EV_FIQ = 28

cdef enum:
    ARM_PC_INCREMENT = 4
    THUMB_PC_INCREMENT = 2

