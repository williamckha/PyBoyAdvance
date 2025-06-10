from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pyboy_advance.memory.memory import MemoryAccess
from pyboy_advance.utils import get_bit, get_bits, sign_32, interpret_signed_32, interpret_signed_64

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


class MultiplyLongOpcode(IntEnum):
    UMULL = 0b00
    UMLAL = 0b01
    SMULL = 0b10
    SMLAL = 0b11


def arm_multiply(cpu: CPU, instr: int):
    """Execute a Multiply instruction"""

    rd = get_bits(instr, 16, 19)  # Destination reg
    rn = get_bits(instr, 12, 15)  # Accumulate reg
    rs = get_bits(instr, 8, 11)  # Operand reg
    rm = get_bits(instr, 0, 3)  # Operand reg

    accumulate = get_bit(instr, 21)
    set_cond_codes = get_bit(instr, 20)

    if accumulate:
        cpu.regs[rd] = (cpu.regs[rm] * cpu.regs[rs] + cpu.regs[rn]) & 0xFFFFFFFF
    else:
        cpu.regs[rd] = (cpu.regs[rm] * cpu.regs[rs]) & 0xFFFFFFFF

    if set_cond_codes:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0

    cpu.arm_advance_pc()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL


def arm_multiply_long(cpu: CPU, instr: int):
    """Execute a Multiply Long instruction"""

    rd_hi = get_bits(instr, 16, 19)  # Upper bits of destination reg
    rd_lo = get_bits(instr, 12, 15)  # Lower bits of destination reg
    rs = get_bits(instr, 8, 11)  # Operand reg
    rm = get_bits(instr, 0, 3)  # Operand reg

    opcode = get_bits(instr, 21, 22)
    set_cond_codes = get_bit(instr, 20)

    if opcode == MultiplyLongOpcode.UMULL:
        result = cpu.regs[rm] * cpu.regs[rs]
    elif opcode == MultiplyLongOpcode.UMLAL:
        result = (cpu.regs[rd_hi] << 32) | cpu.regs[rd_lo]
        result += cpu.regs[rm] * cpu.regs[rs]
    elif opcode == MultiplyLongOpcode.SMULL:
        result = interpret_signed_32(cpu.regs[rm]) * interpret_signed_32(cpu.regs[rs])
    elif opcode == MultiplyLongOpcode.SMLAL:
        result = interpret_signed_64((cpu.regs[rd_hi] << 32) | cpu.regs[rd_lo])
        result += interpret_signed_32(cpu.regs[rm]) * interpret_signed_32(cpu.regs[rs])
    else:
        raise ValueError

    cpu.regs[rd_lo] = result & 0xFFFFFFFF
    cpu.regs[rd_hi] = (result >> 32) & 0xFFFFFFFF

    if set_cond_codes:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd_hi])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd_hi] == 0 and cpu.regs[rd_lo] == 0

    cpu.arm_advance_pc()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL
