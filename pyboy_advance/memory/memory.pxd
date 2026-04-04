cimport cython

from libc.stdint cimport uint8_t, uint32_t
from cpython.array cimport array

from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.cpu.constants cimport CPUState
from pyboy_advance.memory.constants cimport MemoryRegion, MemoryAccess
from pyboy_advance.memory.gamepak cimport GamePak
from pyboy_advance.memory.io cimport IO
from pyboy_advance.scheduler cimport Scheduler
from pyboy_advance.utils cimport (
    get_bit,
    array_read_16,
    array_read_32,
    array_write_32,
    array_write_16,
    ror_32,
    extend_sign_16,
    extend_sign_8,
    get_bits,
)

cdef class Memory:
    cdef Scheduler scheduler
    cdef CPU cpu
    cdef IO io
    cdef uint8_t[:] bios
    cdef uint8_t[:] ewram
    cdef uint8_t[:] iwram
    cdef GamePak gamepak
    cdef uint32_t bios_last_opcode
    cdef WaitstateControlRegister wait_control
    cdef int[2][16] access_time_32
    cdef int[2][16] access_time_16

    cdef uint32_t read_32(self, uint32_t, int) noexcept
    cdef uint32_t read_32_ror(self, uint32_t, int) noexcept
    cdef uint32_t read_16(self, uint32_t, int) noexcept
    cdef uint32_t read_16_signed(self, uint32_t, int) noexcept
    cdef uint32_t read_16_ror(self, uint32_t, int) noexcept
    cdef uint32_t read_8(self, uint32_t, int) noexcept
    cdef uint32_t read_8_signed(self, uint32_t, int) noexcept
    cdef void write_32(self, uint32_t, uint32_t, int) noexcept
    cdef void write_16(self, uint32_t, uint32_t, int) noexcept
    cdef void write_8(self, uint32_t, uint32_t, int) noexcept
    cdef uint32_t _read_32_internal(self, uint32_t, int) noexcept
    cdef uint32_t _read_16_internal(self, uint32_t, int) noexcept
    cdef uint32_t _read_8_internal(self, uint32_t, int) noexcept
    cdef void _write_32_internal(self, uint32_t, uint32_t, int) noexcept
    cdef void _write_16_internal(self, uint32_t, uint32_t, int) noexcept
    cdef void _write_8_internal(self, uint32_t, uint32_t, int) noexcept
    cdef uint32_t read_unused_memory(self) noexcept
    cdef void _init_access_times(self) noexcept
    cdef void update_waitstates(self) noexcept

    @cython.locals(cycles=int)
    cdef void _idle_for_access(self, uint32_t, int, int) noexcept

cdef class WaitstateControlRegister:
    cdef int[4] NON_SEQUENTIAL_CYCLES
    cdef uint32_t reg

    cdef int get_sram(self) noexcept
    cdef int get_ws0_non_seq(self) noexcept
    cdef int get_ws0_seq(self) noexcept
    cdef int get_ws1_non_seq(self) noexcept
    cdef int get_ws1_seq(self) noexcept
    cdef int get_ws2_non_seq(self) noexcept
    cdef int get_ws2_seq(self) noexcept