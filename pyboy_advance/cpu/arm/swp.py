from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import get_bit, get_bits

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_single_data_swap(cpu: CPU, instr: int):
    """Executes a Single Data Swap instruction (SWP)"""

    base_reg = get_bits(instr, 16, 19)
    dst_reg = get_bits(instr, 12, 15)
    src_reg = get_bits(instr, 0, 3)

    byte_word_bit = get_bit(instr, 22)

    if byte_word_bit:  # Byte swap
        temp = cpu.memory.read_8(cpu.regs[base_reg], MemoryAccess.NON_SEQUENTIAL)
        cpu.memory.write_8(cpu.regs[base_reg], cpu.regs[src_reg], MemoryAccess.NON_SEQUENTIAL)
        cpu.regs[dst_reg] = temp
    else:  # Word swap
        temp = cpu.memory.read_32_ror(cpu.regs[base_reg], MemoryAccess.NON_SEQUENTIAL)
        cpu.memory.write_32(cpu.regs[base_reg], cpu.regs[src_reg], MemoryAccess.NON_SEQUENTIAL)
        cpu.regs[dst_reg] = temp

    cpu.scheduler.idle()

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL
