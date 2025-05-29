from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.constants import CPUState
from pyboy_advance.utils import interpret_signed_24, get_bit, add_int32_to_uint32

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_branch(cpu: CPU, instr: int):
    """Execute a Branch or Branch and Link instruction"""

    offset = interpret_signed_24((instr & 0xFFFFFF)) * 4
    link_flag = get_bit(instr, 24)

    if link_flag:
        cpu.regs.lr = add_int32_to_uint32(cpu.regs.pc, -4)

    cpu.regs.pc = add_int32_to_uint32(cpu.regs.pc, offset)
    cpu.flush_pipeline()


def arm_branch_exchange(cpu: CPU, instr: int):
    """Execute a Branch and Exchange instruction"""

    address = cpu.regs[instr & 0xF]

    # Mask out the last bit indicating whether to switch to THUMB mode
    cpu.regs.pc = address & ~1
    cpu.regs.cpsr.state = CPUState(get_bit(address, 0))
    cpu.flush_pipeline()
