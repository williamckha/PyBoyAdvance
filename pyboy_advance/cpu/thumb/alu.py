from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.constants import CPUState
from pyboy_advance.memory.memory import MemoryAccess
from pyboy_advance.utils import get_bits, get_bit, sign_32, add_uint32_to_uint32

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_move_shifted_register(cpu: CPU, instr: int):
    rs = get_bits(instr, 3, 5)
    rd = get_bits(instr, 0, 2)

    cpu.regs[rd] = cpu.regs[rs]
    cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
    cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0

    cpu.thumb_advance_pc()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_add_subtract(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_move_compare_add_subtract(cpu: CPU, instr: int):
    rd = get_bits(instr, 8, 10)
    immediate_value = get_bits(instr, 0, 7)

    opcode = get_bits(instr, 11, 12)
    if opcode == 0:
        cpu.regs[rd] = immediate_value
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0

    cpu.thumb_advance_pc()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_alu(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_high_reg_branch_exchange(cpu: CPU, instr: int):
    rs = get_bits(instr, 3, 6)
    opcode = get_bits(instr, 8, 9)

    if opcode == 3:
        address = cpu.regs[rs]

        # Mask out the last bit indicating whether to switch to THUMB mode
        cpu.regs.pc = address & ~1
        cpu.regs.cpsr.state = CPUState(get_bit(address, 0))
        cpu.flush_pipeline()


def thumb_load_address(cpu: CPU, instr: int):
    opcode = get_bit(instr, 11)
    rd = get_bits(instr, 8, 10)
    offset = get_bits(instr, 0, 7) << 2

    if opcode:
        cpu.regs[rd] = add_uint32_to_uint32(cpu.regs.sp, offset)
    else:
        cpu.regs[rd] = add_uint32_to_uint32(cpu.regs.pc & 0xFFFFFFFC, offset)

    cpu.thumb_advance_pc()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_add_offset_to_stack_pointer(cpu: CPU, instr: int):
    raise NotImplementedError
