cimport cython

from libc.stdint cimport uint32_t

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
from pyboy_advance.memory.memory cimport Memory
from pyboy_advance.memory.constants cimport MemoryAccess
from pyboy_advance.utils cimport (
    get_bits,
    get_bit,
    ror_32,
    add_32,
    extend_sign_32,
)

cdef class CPU

ctypedef void (*InstrHandler)(CPU, uint32_t) noexcept

ctypedef InstrHandler (*InstrDecoder)(uint32_t) noexcept

cdef struct InstrPattern:
    uint32_t mask
    uint32_t value
    InstrHandler handler

cdef class CPU:
    cdef Registers regs
    cdef Memory memory
    cdef uint32_t[2] pipeline
    cdef int next_fetch_access
    cdef InstrDecoder arm_decoder
    cdef InstrDecoder thumb_decoder

    cdef void step(self) noexcept
    cdef void step_arm(self) noexcept
    cdef void step_thumb(self) noexcept
    cdef void advance_pc_arm(self) noexcept
    cdef void advance_pc_thumb(self) noexcept
    cdef void flush_pipeline(self) noexcept
    cdef void switch_mode(self, int) noexcept
    cdef void interrupt(self, int) noexcept
    cdef bint check_condition(self, int) noexcept

    @cython.locals(shift_amount=uint32_t)
    cdef (uint32_t, bint) decode_and_compute_shift(self, uint32_t, uint32_t) noexcept

    @cython.locals(result=uint32_t, mask=uint32_t)
    cdef (uint32_t, bint) compute_shift(self, uint32_t, int, uint32_t, bint) noexcept
