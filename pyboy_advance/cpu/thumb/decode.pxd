from libc.stdint cimport uint32_t

from pyboy_advance.cpu.thumb.alu cimport (
    thumb_move_shifted_register,
    thumb_add_subtract,
    thumb_move_compare_add_subtract,
    thumb_alu,
    thumb_high_reg_branch_exchange,
    thumb_add_offset_to_stack_pointer,
    thumb_get_address,
)
from pyboy_advance.cpu.thumb.bdt cimport (
    thumb_multiple_load_store,
    thumb_push_pop_registers,
)
from pyboy_advance.cpu.thumb.branch cimport (
    thumb_unconditional_branch,
    thumb_conditional_branch,
    thumb_long_branch_with_link,
)
from pyboy_advance.cpu.thumb.sdt cimport (
    thumb_pc_relative_load,
    thumb_load_store_sign_extended,
    thumb_load_store_register_offset,
    thumb_load_store_immediate_offset,
    thumb_load_store_halfword,
    thumb_sp_relative_load_store,
)
from pyboy_advance.cpu.thumb.swi cimport thumb_software_interrupt
from pyboy_advance.cpu.arm.decode cimport InstrHandler, InstrPattern

cdef InstrPattern[19] THUMB_PATTERNS

cdef InstrHandler[4096] THUMB_LUT

cdef void fill_thumb_lut() noexcept

cdef InstrHandler thumb_decode(uint32_t) except NULL
