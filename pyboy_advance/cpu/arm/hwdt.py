from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pyboy_advance.memory.memory import MemoryAccess
from pyboy_advance.utils import get_bits, get_bit, add_int_to_uint

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
    rn = get_bits(instr, 16, 19)  # Base reg
    rd = get_bits(instr, 12, 15)  # Source/dest reg

    pre_post_bit = get_bit(instr, 24)
    up_down_bit = get_bit(instr, 23)
    immediate = get_bit(instr, 22)
    write_back = get_bit(instr, 21)
    load_store_bit = get_bit(instr, 20)

    offset = (
        (get_bits(instr, 8, 11) << 4) | get_bits(instr, 0, 3)
        if immediate else
        cpu.regs[get_bits(instr, 0, 3)]
    )

    cpu.arm_advance_pc()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    base = cpu.regs[rn]
    address = add_int_to_uint(base, offset if up_down_bit else -offset)
    effective_address = address if pre_post_bit else base

    opcode = DataTransferOpcode(get_bits(instr, 5, 6))

    if load_store_bit:  # Load

        if not pre_post_bit or write_back:
            cpu.regs[rn] = address

        match opcode:
            case DataTransferOpcode.LDRH:
                cpu.regs[rd] = cpu.memory.read_16_ror(effective_address, MemoryAccess.NON_SEQUENTIAL)
            case DataTransferOpcode.LDRSB:
                cpu.regs[rd] = cpu.memory.read_8(effective_address, MemoryAccess.NON_SEQUENTIAL)
            case DataTransferOpcode.LDRSH:
                if get_bit(effective_address, 0):
                    cpu.regs[rd] = cpu.memory.read_8(effective_address, MemoryAccess.NON_SEQUENTIAL)
                else:
                    cpu.regs[rd] = cpu.memory.read_16(effective_address, MemoryAccess.NON_SEQUENTIAL)

    else:  # Store

        match opcode:
            case DataTransferOpcode.STRH:
                cpu.memory.write_16(effective_address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
            case DataTransferOpcode.LDRD:
                raise NotImplementedError("LDRD not implemented on ARM7")
            case DataTransferOpcode.STRD:
                raise NotImplementedError("STRD not implemented on ARM7")

        if not pre_post_bit or write_back:
            cpu.regs[rn] = address
