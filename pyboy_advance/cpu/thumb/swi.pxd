from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void thumb_software_interrupt(CPU, uint32_t) noexcept
