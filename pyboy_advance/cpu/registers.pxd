cimport cython

from libc.stdint cimport uint32_t

from pyboy_advance.cpu.constants cimport CPUMode, CPUState, BankIndex
from pyboy_advance.utils cimport get_bit, set_bit


@cython.collection_type("sequence")
cdef class Registers:
    cdef int SP, LR, PC
    cdef int BANKED_GPR_RANGE_START
    cdef int BANKED_GPR_RANGE_END
    cdef int BANKED_GPR_RANGE_LEN

    cdef uint32_t[:] regs
    cdef ProgramStatusRegister cpsr
    cdef ProgramStatusRegister spsr
    cdef uint32_t[:] banked_old_gpr
    cdef uint32_t[:] banked_fiq_gpr
    cdef uint32_t[:] banked_sp
    cdef uint32_t[:] banked_lr
    cdef ProgramStatusRegister banked_spsr_fiq
    cdef ProgramStatusRegister banked_spsr_irq
    cdef ProgramStatusRegister banked_spsr_swi
    cdef ProgramStatusRegister banked_spsr_abort
    cdef ProgramStatusRegister banked_spsr_undefined

    cdef uint32_t get(self, uint32_t) noexcept
    cdef void set(self, uint32_t, uint32_t) noexcept
    cdef uint32_t get_sp(self) noexcept
    cdef void set_sp(self, uint32_t) noexcept
    cdef uint32_t get_lr(self) noexcept
    cdef void set_lr(self, uint32_t) noexcept
    cdef uint32_t get_pc(self) noexcept
    cdef void set_pc(self, uint32_t) noexcept
    cdef void switch_mode(self, int) noexcept
    cdef int get_bank_index(self, int) noexcept
    cdef ProgramStatusRegister get_banked_spsr(self, int) noexcept


cdef class ProgramStatusRegister:
    cdef uint32_t reg
    cdef int get_mode(self) noexcept
    cdef void set_mode(self, int) noexcept
    cdef int get_state(self) noexcept
    cdef void set_state(self, int) noexcept
    cdef bint get_sign_flag(self) noexcept
    cdef void set_sign_flag(self, bint) noexcept
    cdef bint get_zero_flag(self) noexcept
    cdef void set_zero_flag(self, bint) noexcept
    cdef bint get_carry_flag(self) noexcept
    cdef void set_carry_flag(self, bint) noexcept
    cdef bint get_overflow_flag(self) noexcept
    cdef void set_overflow_flag(self, bint) noexcept
    cdef bint get_sticky_overflow_flag(self) noexcept
    cdef void set_sticky_overflow_flag(self, bint) noexcept
    cdef bint get_irq_disable(self) noexcept
    cdef void set_irq_disable(self, bint) noexcept
    cdef bint get_fiq_disable(self) noexcept
    cdef void set_fiq_disable(self, bint) noexcept
