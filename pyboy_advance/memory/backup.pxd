from libc.stdint cimport uint8_t, uint32_t
from cpython.array cimport array

from pyboy_advance.memory.constants cimport (
    MemoryRegion,
    FlashState,
    FlashCommand,
    FlashCommandAddress,
    BackupStorageType,
    FlashManufacturerID,
    FlashDeviceID,
)

cdef class Flash

cdef class BackupStorage:
    cdef BackupStorageType type
    cdef uint8_t[:] sram
    cdef Flash flash

    cdef uint32_t read_8(self, uint32_t) noexcept
    cdef void write_8(self, uint32_t, uint32_t) noexcept

cdef class Flash:
    cdef BackupStorage backup_storage
    cdef uint8_t[:] storage
    cdef FlashState flash_state
    cdef bint identification_mode
    cdef bint bank

    cdef uint32_t read_8(self, uint32_t) noexcept
    cdef void write_8(self, uint32_t, uint32_t) noexcept
