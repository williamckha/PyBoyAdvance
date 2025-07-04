from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.registers import Registers
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import get_bit, get_bits, add_int32_to_uint32

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_single_data_transfer(cpu: CPU, instr: int):
    """Execute a Single Data Transfer instruction (LDR, STR)"""

    rn = get_bits(instr, 16, 19)  # Base reg
    rd = get_bits(instr, 12, 15)  # Source/dest reg

    immediate_bit = get_bit(instr, 25)
    pre_post_bit = get_bit(instr, 24)
    up_down_bit = get_bit(instr, 23)
    byte_word_bit = get_bit(instr, 22)
    write_back_bit = get_bit(instr, 21)
    load_store_bit = get_bit(instr, 20)

    if immediate_bit:
        rm = get_bits(instr, 0, 3)
        shift = get_bits(instr, 4, 11)
        offset, _ = cpu.decode_and_compute_shift(cpu.regs[rm], shift)
    else:
        offset = get_bits(instr, 0, 11)

    base = cpu.regs[rn]
    address = add_int32_to_uint32(base, offset if up_down_bit else -offset)
    effective_address = address if pre_post_bit else base

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    if load_store_bit:  # Load
        if byte_word_bit:
            # Load byte
            value = cpu.memory.read_8(effective_address, MemoryAccess.NON_SEQUENTIAL)
        else:
            # Load word
            value = cpu.memory.read_32_ror(effective_address, MemoryAccess.NON_SEQUENTIAL)

        # When post-indexing, write back is always enabled
        # When pre-indexing, write back is optional (controlled by W bit)
        if not pre_post_bit or write_back_bit:
            cpu.regs[rn] = address

        cpu.regs[rd] = value

        cpu.scheduler.idle()

        if rd == Registers.PC:
            cpu.flush_pipeline()

    else:  # Store
        if byte_word_bit:
            # Store byte
            cpu.memory.write_8(effective_address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
        else:
            # Store word
            cpu.memory.write_32(effective_address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)

        # When post-indexing, write back is always enabled
        # When pre-indexing, write back is optional (controlled by W bit)
        if not pre_post_bit or write_back_bit:
            cpu.regs[rn] = address
