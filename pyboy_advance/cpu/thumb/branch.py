from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.constants import Condition
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import (
    get_bits,
    interpret_signed_12,
    add_int32_to_uint32,
    interpret_signed_8,
    get_bit,
    add_uint32_to_uint32,
    interpret_signed_23,
)

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_unconditional_branch(cpu: CPU, instr: int):
    """Execute a THUMB.18 instruction (unconditional branch)"""

    offset = interpret_signed_12(get_bits(instr, 0, 10) << 1)
    cpu.regs.pc = add_int32_to_uint32(cpu.regs.pc, offset)
    cpu.flush_pipeline()


def thumb_conditional_branch(cpu: CPU, instr: int):
    """Execute a THUMB.16 instruction (conditional branch)"""

    condition = Condition(get_bits(instr, 8, 11))
    offset = interpret_signed_8(get_bits(instr, 0, 7)) * 2

    if cpu.check_condition(condition):
        cpu.regs.pc = add_int32_to_uint32(cpu.regs.pc, offset)
        cpu.flush_pipeline()
    else:
        cpu.advance_pc_thumb()
        cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_long_branch_with_link(cpu: CPU, instr: int):
    """
    Execute a THUMB.19 instruction (long branch with link).

    Long Branch with Link is a 32-bit instruction split across two 16-bit THUMB opcodes.
    Bit 11 determines whether the opcode is the first one or the second one.
    """

    is_first_opcode = not get_bit(instr, 11)
    if is_first_opcode:
        address_upper_bits = interpret_signed_23(get_bits(instr, 0, 10) << 12)
        cpu.regs.lr = add_int32_to_uint32(cpu.regs.pc, address_upper_bits)
        cpu.advance_pc_thumb()
        cpu.next_fetch_access = MemoryAccess.SEQUENTIAL
    else:
        address_lower_bits = get_bits(instr, 0, 10) << 1
        pc = add_int32_to_uint32(cpu.regs.pc, -2)
        cpu.regs.pc = add_uint32_to_uint32(cpu.regs.lr, address_lower_bits)
        cpu.regs.lr = pc | 1
        cpu.flush_pipeline()
