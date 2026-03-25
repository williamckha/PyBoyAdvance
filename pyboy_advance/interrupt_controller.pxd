cimport cython

from libc.stdint cimport uint32_t

from pyboy_advance.constants cimport Interrupt, PowerDownMode

cdef class InterruptController:
    cdef int WRITE_INTERRUPT_REGISTERS_DELAY
    cdef int UPDATE_IRQ_LINE_DELAY

    cdef uint32_t _interrupt_enable
    cdef uint32_t _interrupt_flags
    cdef bint _interrupt_master_enable
    cdef uint32_t _pending_interrupt_enable
    cdef uint32_t _pending_interrupt_flags
    cdef bint _pending_interrupt_master_enable
    cdef bint irq_line
    cdef int power_down_mode

    cdef uint32_t get_interrupt_enable(self) noexcept
    cdef void set_interrupt_enable(self, uint32_t) noexcept
    cdef uint32_t get_interrupt_flags(self) noexcept
    cdef void set_interrupt_flags(self, uint32_t) noexcept
    cdef bint get_interrupt_master_enable(self) noexcept
    cdef void set_interrupt_master_enable(self, bint) noexcept
    cdef void signal(self, int) noexcept
    cdef void _schedule_write_interrupt_registers(self) noexcept

    @cython.locals(new_irq_line=bint)
    cdef void _write_interrupt_registers(self) noexcept

    cdef void _set_irq_line(self) noexcept
    cdef void _reset_irq_line(self) noexcept
