from libc.stdint cimport uint32_t

from pyboy_advance.cpu.arm.decode cimport arm_decode
from pyboy_advance.cpu.constants cimport (
    CPUMode,
    CPUState,
    Condition,
    ARM_PC_INCREMENT,
    THUMB_PC_INCREMENT,
    ShiftType,
    ExceptionVector,
)
from pyboy_advance.cpu.registers cimport Registers
from pyboy_advance.cpu.thumb.decode cimport thumb_decode
from pyboy_advance.memory.memory cimport Memory
from pyboy_advance.memory.constants cimport MemoryAccess
from pyboy_advance.utils cimport (
    get_bits,
    get_bit,
    ror_32,
    add_32,
    extend_sign_32,
)

cdef class CPU:
    cdef Registers regs
    cdef Memory memory