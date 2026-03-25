# ifndef CYTHON
from __future__ import annotations

from pyboy_advance.cpu.thumb.alu import (
    thumb_move_shifted_register,
    thumb_add_subtract,
    thumb_move_compare_add_subtract,
    thumb_alu,
    thumb_high_reg_branch_exchange,
    thumb_add_offset_to_stack_pointer,
    thumb_get_address,
)
from pyboy_advance.cpu.thumb.bdt import (
    thumb_multiple_load_store,
    thumb_push_pop_registers,
)
from pyboy_advance.cpu.thumb.branch import (
    thumb_unconditional_branch,
    thumb_conditional_branch,
    thumb_long_branch_with_link,
)
from pyboy_advance.cpu.thumb.sdt import (
    thumb_pc_relative_load,
    thumb_load_store_sign_extended,
    thumb_load_store_register_offset,
    thumb_load_store_immediate_offset,
    thumb_load_store_halfword,
    thumb_sp_relative_load_store,
)
from pyboy_advance.cpu.thumb.swi import thumb_software_interrupt
from pyboy_advance.cpu.arm.decode import InstrHandler, InstrPattern
# endif


THUMB_PATTERNS: list[InstrPattern] = [
    # ----------+------------+------------+------------------------------------
    #           | Mask       | Value      | Handler
    # ----------+------------+------------+------------------------------------
    InstrPattern(0b1111_1111, 0b1101_1111, thumb_software_interrupt),
    InstrPattern(0b1111_1000, 0b1110_0000, thumb_unconditional_branch),
    InstrPattern(0b1111_0000, 0b1101_0000, thumb_conditional_branch),
    InstrPattern(0b1111_0000, 0b1111_0000, thumb_long_branch_with_link),
    InstrPattern(0b1111_0000, 0b1100_0000, thumb_multiple_load_store),
    InstrPattern(0b1111_0110, 0b1011_0100, thumb_push_pop_registers),
    InstrPattern(0b1111_1111, 0b1011_0000, thumb_add_offset_to_stack_pointer),
    InstrPattern(0b1111_0000, 0b1010_0000, thumb_get_address),
    InstrPattern(0b1111_0000, 0b1001_0000, thumb_sp_relative_load_store),
    InstrPattern(0b1111_0000, 0b1000_0000, thumb_load_store_halfword),
    InstrPattern(0b1110_0000, 0b0110_0000, thumb_load_store_immediate_offset),
    InstrPattern(0b1111_0010, 0b0101_0000, thumb_load_store_register_offset),
    InstrPattern(0b1111_0010, 0b0101_0010, thumb_load_store_sign_extended),
    InstrPattern(0b1111_1000, 0b0100_1000, thumb_pc_relative_load),
    InstrPattern(0b1111_1100, 0b0100_0100, thumb_high_reg_branch_exchange),
    InstrPattern(0b1111_1100, 0b0100_0000, thumb_alu),
    InstrPattern(0b1110_0000, 0b0010_0000, thumb_move_compare_add_subtract),
    InstrPattern(0b1111_1000, 0b0001_1000, thumb_add_subtract),
    InstrPattern(0b1110_0000, 0b0000_0000, thumb_move_shifted_register),
]


# ifndef CYTHON
THUMB_LUT: list[InstrHandler | None] = [None] * (2**8)
# endif


def fill_thumb_lut():
    for opcode in range(2**8):
        for pattern in THUMB_PATTERNS:
            if (opcode & pattern.mask) == pattern.value:
                THUMB_LUT[opcode] = pattern.handler
                break


fill_thumb_lut()


def thumb_decoder(instr: int) -> InstrHandler:
    instruction_handler = THUMB_LUT[instr >> 8]
    if not instruction_handler:
        raise ValueError(f"Unknown THUMB instruction: {instr:016b}")
    return instruction_handler
