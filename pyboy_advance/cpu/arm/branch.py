# ifndef CYTHON
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU

from pyboy_advance.utils import extend_sign_24, get_bit, add_32
# endif


def arm_branch(cpu: CPU, instr: int):
    """Execute a Branch or Branch and Link instruction"""

    offset = extend_sign_24((instr & 0xFFFFFF)) * 4
    link_flag = get_bit(instr, 24)

    if link_flag:
        cpu.regs.lr = add_32(cpu.regs.pc, -4)

    cpu.regs.pc = add_32(cpu.regs.pc, offset)
    cpu.flush_pipeline()


def arm_branch_exchange(cpu: CPU, instr: int):
    """Execute a Branch and Exchange instruction"""

    address = cpu.regs.get(instr & 0xF)

    # Mask out the last bit indicating whether to switch to THUMB mode
    cpu.regs.pc = address & ~1
    cpu.regs.cpsr.state = get_bit(address, 0)
    cpu.flush_pipeline()
