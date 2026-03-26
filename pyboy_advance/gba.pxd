cimport cython

from pyboy_advance.app.constants cimport WindowEvent
from pyboy_advance.app.window cimport Window
from pyboy_advance.cpu.constants cimport ExceptionVector, BankIndex
from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.interrupt_controller cimport InterruptController
from pyboy_advance.keypad cimport Keypad
from pyboy_advance.memory.dma cimport DMAController
from pyboy_advance.memory.gamepak cimport GamePak
from pyboy_advance.memory.io cimport IO
from pyboy_advance.memory.memory cimport Memory
from pyboy_advance.ppu.ppu cimport PPU
from pyboy_advance.scheduler cimport Scheduler
from pyboy_advance.cpu.arm.decode cimport arm_decoder
from pyboy_advance.cpu.thumb.decode cimport thumb_decoder

cdef class PyBoyAdvance:
    cdef GamePak gamepak
    cdef Scheduler scheduler
    cdef Memory memory
    cdef InterruptController interrupt_controller
    cdef DMAController dma_controller
    cdef PPU ppu
    cdef Keypad keypad
    cdef readonly CPU cpu

    cpdef void step(self)

    cpdef void frame(self)

    @cython.locals(window=Window, event=int)
    cpdef void run(self)
