from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pyboy_advance.cpu.registers import Registers
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import get_bits, get_bit, add_int32_to_uint32

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


class DataTransferOpcode(IntEnum):
    STRH = 1  # Store halfword
    LDRD = 2  # Load doubleword
    STRD = 3  # Store doubleword

    LDRH = 1  # Load unsigned halfword
    LDRSB = 2  # Load signed byte
    LDRSH = 3  # Load signed halfword


def arm_halfword_data_transfer(cpu: CPU, instr: int):
    """Execute a Halfword Data Transfer instruction (LDRH, STRH, etc.)"""

    rn = get_bits(instr, 16, 19)  # Base reg
    rd = get_bits(instr, 12, 15)  # Source/dest reg

    pre_post_bit = get_bit(instr, 24)
    up_down_bit = get_bit(instr, 23)
    immediate_bit = get_bit(instr, 22)
    write_back_bit = get_bit(instr, 21)
    load_store_bit = get_bit(instr, 20)

    offset = (
        (get_bits(instr, 8, 11) << 4) | get_bits(instr, 0, 3)
        if immediate_bit
        else cpu.regs[get_bits(instr, 0, 3)]
    )

    base = cpu.regs[rn]
    address = add_int32_to_uint32(base, offset if up_down_bit else -offset)
    effective_address = address if pre_post_bit else base

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    opcode = DataTransferOpcode(get_bits(instr, 5, 6))

    if load_store_bit:  # Load
        # When post-indexing, write back is always enabled
        # When pre-indexing, write back is optional (controlled by W bit)
        if not pre_post_bit or write_back_bit:
            cpu.regs[rn] = address

        if opcode == DataTransferOpcode.LDRH:
            cpu.regs[rd] = cpu.memory.read_16_ror(effective_address, MemoryAccess.NON_SEQUENTIAL)
        elif opcode == DataTransferOpcode.LDRSB:
            cpu.regs[rd] = cpu.memory.read_8_signed(effective_address, MemoryAccess.NON_SEQUENTIAL)
        elif opcode == DataTransferOpcode.LDRSH:
            cpu.regs[rd] = cpu.memory.read_16_signed(effective_address, MemoryAccess.NON_SEQUENTIAL)

        cpu.scheduler.idle()

        if rd == Registers.PC:
            cpu.flush_pipeline()

    else:  # Store
        if opcode == DataTransferOpcode.STRH:
            cpu.memory.write_16(effective_address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
        elif opcode == DataTransferOpcode.LDRD:
            raise NotImplementedError("LDRD not implemented on ARM7")
        elif opcode == DataTransferOpcode.STRD:
            raise NotImplementedError("STRD not implemented on ARM7")

        # When post-indexing, write back is always enabled
        # When pre-indexing, write back is optional (controlled by W bit)
        if not pre_post_bit or write_back_bit:
            cpu.regs[rn] = address
