from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.constants import ARMCondition
from pyboy_advance.memory.memory import MemoryAccess
from pyboy_advance.utils import get_bits, interpret_signed_12, add_int32_to_uint32, interpret_signed_8, get_bit, \
    add_uint32_to_uint32

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_unconditional_branch(cpu: CPU, instr: int):
    offset = interpret_signed_12(get_bits(instr, 0, 10) << 1)
    cpu.regs.pc = add_int32_to_uint32(cpu.regs.pc, offset)
    cpu.flush_pipeline()


def thumb_conditional_branch(cpu: CPU, instr: int):
    condition = ARMCondition(get_bits(instr, 8, 11))
    offset = interpret_signed_8(get_bits(instr, 0, 7) << 1)

    if cpu.check_condition(condition):
        cpu.regs.pc = add_int32_to_uint32(cpu.regs.pc, offset)
        cpu.flush_pipeline()
    else:
        cpu.thumb_advance_pc()
        cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_long_branch_with_link(cpu: CPU, instr: int):
    # Long Branch with Link is a 32-bit instruction split across
    # two 16-bit THUMB opcodes
    is_first_opcode = not get_bit(instr, 11)
    if is_first_opcode:
        address_upper_bits = get_bits(instr, 0, 10) << 12
        cpu.regs.lr = add_uint32_to_uint32(cpu.regs.pc, address_upper_bits)

        cpu.thumb_advance_pc()
        cpu.next_fetch_access = MemoryAccess.SEQUENTIAL
    else:
        address_lower_bits = get_bits(instr, 0, 10) << 1
        target_address = add_uint32_to_uint32(cpu.regs.lr, address_lower_bits)
        cpu.regs.lr = (cpu.regs.pc - 2) | 1
        cpu.regs.pc = target_address
        cpu.flush_pipeline()
