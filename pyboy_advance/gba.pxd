cimport cython

from libc.stdint cimport int64_t
from cpython.time cimport perf_counter_ns

from pyboy_advance.app.constants cimport WindowEvent
from pyboy_advance.app.window cimport Window
from pyboy_advance.constants cimport CLOCK_SPEED_HZ, NANOSECONDS_PER_SECOND, EventTrigger
from pyboy_advance.cpu.constants cimport ExceptionVector, BankIndex
from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.cpu.arm.decode cimport arm_decoder
from pyboy_advance.cpu.thumb.decode cimport thumb_decoder
from pyboy_advance.interrupt_controller cimport InterruptController
from pyboy_advance.keypad cimport Keypad
from pyboy_advance.memory.dma cimport DMAController
from pyboy_advance.memory.gamepak cimport GamePak
from pyboy_advance.memory.io cimport IO
from pyboy_advance.memory.memory cimport Memory
from pyboy_advance.ppu.constants cimport CYCLES_FRAME
from pyboy_advance.ppu.ppu cimport PPU
from pyboy_advance.scheduler cimport Scheduler
from pyboy_advance.timer cimport Timers

cdef class PyBoyAdvance:
    cdef GamePak gamepak
    cdef Scheduler scheduler
    cdef Memory memory
    cdef InterruptController interrupt_controller
    cdef DMAController dma_controller
    cdef Timers timers
    cdef PPU ppu
    cdef Keypad keypad
    cdef readonly CPU cpu

    cdef int64_t _time_per_frame
    cdef int64_t _last_frame_time
    cdef int64_t _accumulated_time

    cpdef void step(self) noexcept

    cpdef void frame(self) noexcept

    @cython.locals(window=Window, event=int)
    cpdef void run(self) noexcept

    cpdef void set_emulation_speed(self, float speed)

    cdef void _frame_limiter(self) noexcept
