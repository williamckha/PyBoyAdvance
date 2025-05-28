from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.registers import Registers
from pyboy_advance.memory.memory import MemoryAccess
from pyboy_advance.utils import get_bit, get_bits, add_int_to_uint

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_single_data_transfer(cpu: CPU, instr: int):
    rn = get_bits(instr, 16, 19)
    rd = get_bits(instr, 12, 15)

    immediate = not get_bit(instr, 25)
    if immediate:
        rm = get_bits(instr, 0, 3)
        shift = get_bits(instr, 4, 11)
        offset, _ = cpu.compute_shift(cpu.regs[rm], shift)
    else:
        offset = get_bits(instr, 0, 11)

    cpu.arm_advance_pc()

    pre_post_bit = get_bit(instr, 24)
    up_down_bit = get_bit(instr, 23)
    byte_word_bit = get_bit(instr, 22)
    load_store_bit = get_bit(instr, 20)

    base = cpu.regs[rn]
    address = add_int_to_uint(base, offset if up_down_bit else -offset)
    effective_address = address if pre_post_bit else base

    if load_store_bit:  # Load

        if byte_word_bit:
            # Load byte
            value = cpu.memory.read_8(effective_address, MemoryAccess.NON_SEQUENTIAL)
        else:
            # Load word
            value = cpu.memory.read_32_ror(effective_address, MemoryAccess.NON_SEQUENTIAL)

        if pre_post_bit:
            write_back_bit = get_bit(instr, 21)
            if write_back_bit:
                cpu.regs[rn] = address

        cpu.regs[rd] = value

        if rd == Registers.PC:
            cpu.flush_pipeline()

    else:  # Store

        if byte_word_bit:
            # Store byte
            cpu.memory.write_8(effective_address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
        else:
            # Store word
            cpu.memory.write_32(effective_address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)

        if pre_post_bit:
            write_back_bit = get_bit(instr, 21)
            if write_back_bit:
                cpu.regs[rn] = address
