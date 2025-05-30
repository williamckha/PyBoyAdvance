from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_move_shifted_register(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_add_subtract(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_move_compare_add_subtract(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_alu(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_high_reg_branch_exchange(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_load_address(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_add_offset_to_stack_pointer(cpu: CPU, instr: int):
    raise NotImplementedError
