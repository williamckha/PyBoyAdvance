from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import InstructionHandler

THUMB_PATTERNS: list[tuple[int, int, InstructionHandler]] = [
    # ---------+-----------+------------------------------------
    # Mask     | Value     | Handler
    # ---------+-----------+------------------------------------
    (0b11111111, 0b11011111, thumb_software_interrupt),
    (0b11111000, 0b11100000, thumb_unconditional_branch),
    (0b11110000, 0b11010000, thumb_conditional_branch),
    (0b11110000, 0b11110000, thumb_long_branch_with_link),
    (0b11110000, 0b11000000, thumb_multiple_load_store),
    (0b11110110, 0b10110100, thumb_push_pop_registers),
    (0b11111111, 0b10110000, thumb_add_offset_to_stack_pointer),
    (0b11110000, 0b10100000, thumb_get_address),
    (0b11110000, 0b10010000, thumb_sp_relative_load_store),
    (0b11110000, 0b10000000, thumb_load_store_halfword),
    (0b11100000, 0b01100000, thumb_load_store_immediate_offset),
    (0b11110010, 0b01010000, thumb_load_store_register_offset),
    (0b11110010, 0b01010010, thumb_load_store_sign_extended),
    (0b11111000, 0b01001000, thumb_pc_relative_load),
    (0b11111100, 0b01000100, thumb_high_reg_branch_exchange),
    (0b11111100, 0b01000000, thumb_alu),
    (0b11100000, 0b00100000, thumb_move_compare_add_subtract),
    (0b11111000, 0b00011000, thumb_add_subtract),
    (0b11100000, 0b00000000, thumb_move_shifted_register),
]

THUMB_LUT: list[InstructionHandler | None] = [None] * 256

for opcode in range(256):
    for mask, value, handler in THUMB_PATTERNS:
        if (opcode & mask) == value:
            THUMB_LUT[opcode] = handler
            break


def thumb_decode(instr: int) -> InstructionHandler:
    instruction_handler = THUMB_LUT[instr >> 8]
    if instruction_handler is None:
        raise ValueError(f"Unknown THUMB instruction: {instr:016b}")
    return instruction_handler
