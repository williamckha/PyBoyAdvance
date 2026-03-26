from libc.stdint cimport uint32_t

from pyboy_advance.constants cimport Interrupt, EventTrigger
from pyboy_advance.memory.memory cimport Memory
from pyboy_advance.memory.constants cimport (
    IOAddress,
    MemoryAccess,
    DMAAddressAdjustment,
    DMAStartTiming,
    DMATransferSize,
)
from pyboy_advance.scheduler cimport Scheduler
from pyboy_advance.utils cimport get_bits, get_bit, set_bit

cdef class DMAControlRegister:
    cdef uint32_t reg

    cdef int get_dst_address_adjustment(self) noexcept
    cdef int get_src_address_adjustment(self) noexcept
    cdef bint get_repeat(self) noexcept
    cdef int get_transfer_size(self) noexcept
    cdef int get_start_timing(self) noexcept
    cdef bint get_irq_when_done(self) noexcept
    cdef bint get_transfer_enabled(self) noexcept
    cdef void set_transfer_enabled(self, bint) noexcept

cdef class DMAChannel:
    cdef uint32_t[4] SRC_MASK
    cdef uint32_t[4] DST_MASK
    cdef uint32_t[4] COUNT_MASK
    cdef int[4] INTERRUPT
    cdef int TRANSFER_DELAY

    cdef int channel_id
    cdef Scheduler scheduler
    cdef Memory memory
    cdef bint fifo
    cdef bint pending
    cdef DMAControlRegister _control_reg
    cdef uint32_t _count
    cdef uint32_t _src
    cdef uint32_t _dst
    cdef uint32_t _internal_count
    cdef uint32_t _internal_src
    cdef uint32_t _internal_dst
    cdef object _event

    cdef uint32_t get_control_reg(self) noexcept
    cdef void set_control_reg(self, uint32_t) noexcept
    cdef uint32_t get_count(self) noexcept
    cdef void set_count(self, uint32_t) noexcept
    cdef uint32_t get_src_address(self) noexcept
    cdef void set_src_address(self, uint32_t) noexcept
    cdef uint32_t get_dst_address(self) noexcept
    cdef void set_dst_address(self, uint32_t) noexcept
    cdef void transfer(self) noexcept
    cdef void activate(self) noexcept

cdef class DMAController:
    cdef DMAChannel channel_0
    cdef DMAChannel channel_1
    cdef DMAChannel channel_2
    cdef DMAChannel channel_3

    cdef bint get_active(self) noexcept
    cdef void perform_transfers(self) noexcept