from libc.stdint cimport uint32_t

from pyboy_advance.app.constants cimport WindowEvent
from pyboy_advance.constants cimport Interrupt, Key
from pyboy_advance.interrupt_controller cimport InterruptController
from pyboy_advance.utils cimport get_bit, get_bits

cdef class Keypad:
    cdef InterruptController interrupt_controller
    cdef KeypadInterruptControlRegister key_control
    cdef uint32_t key_input

    cdef void press_key(self, int) noexcept
    cdef void release_key(self, int) noexcept
    cdef void process_window_event(self, int) noexcept
    cdef bint _evaluate_irq_condition(self) noexcept

cdef class KeypadInterruptControlRegister:
    cdef uint32_t reg

    cdef uint32_t get_key_select(self) noexcept
    cdef bint get_irq_enable(self) noexcept
    cdef bint get_irq_if_all(self) noexcept
