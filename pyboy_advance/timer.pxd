from libc.stdint cimport uint32_t

from pyboy_advance.constants cimport EventTrigger, Interrupt
from pyboy_advance.interrupt_controller cimport InterruptController
from pyboy_advance.scheduler cimport Scheduler, Event
from pyboy_advance.utils cimport get_bit, get_bits, set_bit

cdef class Timers:
    cdef Timer timer_0
    cdef Timer timer_1
    cdef Timer timer_2
    cdef Timer timer_3

cdef class Timer:
    cdef int WRITE_TIMER_REGISTER_DELAY
    cdef int START_TIMER_DELAY
    cdef int[4] FREQUENCIES

    cdef Scheduler scheduler
    cdef InterruptController interrupt_controller
    cdef int interrupt
    cdef Timer next_timer
    cdef uint32_t _counter
    cdef uint32_t _reload_value
    cdef uint32_t _control_reg
    cdef uint32_t _pending_reload_value
    cdef uint32_t _pending_control_reg
    cdef Event _overflow_event

    cdef uint32_t get_counter(self) noexcept
    cdef void set_counter(self, uint32_t) noexcept
    cdef uint32_t get_control_reg(self) noexcept
    cdef void set_control_reg(self, uint32_t) noexcept
    cdef int get_frequency(self) noexcept
    cdef bint get_count_up(self) noexcept
    cdef void set_count_up(self, bint) noexcept
    cdef bint get_irq_enabled(self) noexcept
    cdef bint get_timer_enabled(self) noexcept
    cdef void _write_reload_value(self) noexcept
    cdef void _write_control_reg(self) noexcept
    cdef void _start(self) noexcept
    cdef void _stop(self) noexcept
    cdef void _update_counter(self) noexcept
    cdef void _schedule_overflow_event(self, uint32_t) noexcept
    cdef void _overflow(self) noexcept
