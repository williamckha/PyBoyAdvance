from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from pyboy_advance.cpu.thumb.alu import thumb_move_shifted_register, thumb_add_subtract, \
    thumb_move_compare_add_subtract, thumb_alu, thumb_high_reg_branch_exchange, thumb_add_offset_to_stack_pointer, \
    thumb_load_address
from pyboy_advance.cpu.thumb.bdt import thumb_multiple_load_store, thumb_push_pop_registers
from pyboy_advance.cpu.thumb.branch import thumb_unconditional_branch, thumb_conditional_branch, \
    thumb_long_branch_with_link
from pyboy_advance.cpu.thumb.sdt import thumb_pc_relative_load, thumb_load_store_sign_extended, \
    thumb_load_store_register_offset, thumb_load_store_immediate_offset, thumb_load_store_halfword, \
    thumb_sp_relative_load_store
from pyboy_advance.cpu.thumb.swi import thumb_software_interrupt

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_decode(instr: int) -> Callable[[CPU, int], None]:
    opcode = instr >> 8

    if (opcode & 0b11111111) == 0b11011111:
        return thumb_software_interrupt
    elif (opcode & 0b11111000) == 0b11100000:
        return thumb_unconditional_branch
    elif (opcode & 0b11110000) == 0b11010000:
        return thumb_conditional_branch
    elif (opcode & 0b11110000) == 0b11110000:
        return thumb_long_branch_with_link
    elif (opcode & 0b11110000) == 0b11000000:
        return thumb_multiple_load_store
    elif (opcode & 0b11110110) == 0b10110100:
        return thumb_push_pop_registers
    elif (opcode & 0b11111111) == 0b10110000:
        return thumb_add_offset_to_stack_pointer
    elif (opcode & 0b11110000) == 0b10100000:
        return thumb_load_address
    elif (opcode & 0b11110000) == 0b10010000:
        return thumb_sp_relative_load_store
    elif (opcode & 0b11110000) == 0b10000000:
        return thumb_load_store_halfword
    elif (opcode & 0b11100000) == 0b01100000:
        return thumb_load_store_immediate_offset
    elif (opcode & 0b11110010) == 0b01010000:
        return thumb_load_store_register_offset
    elif (opcode & 0b11110010) == 0b01010010:
        return thumb_load_store_sign_extended
    elif (opcode & 0b11111000) == 0b01001000:
        return thumb_pc_relative_load
    elif (opcode & 0b11111100) == 0b01000100:
        return thumb_high_reg_branch_exchange
    elif (opcode & 0b11111100) == 0b01000000:
        return thumb_alu
    elif (opcode & 0b11100000) == 0b00100000:
        return thumb_move_compare_add_subtract
    elif (opcode & 0b11111000) == 0b00011000:
        return thumb_add_subtract
    elif (opcode & 0b11100000) == 0b00000000:
        return thumb_move_shifted_register

    raise ValueError(f"Unknown THUMB instruction: {instr:016b}")
