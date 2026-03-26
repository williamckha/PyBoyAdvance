# ifndef CYTHON
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU

from pyboy_advance.cpu.arm.constants import MultiplyLongOpcode
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import get_bit, get_bits, sign_32, extend_sign_32
# endif


def arm_multiply(cpu: CPU, instr: int):
    """Execute a Multiply instruction"""

    rd = get_bits(instr, 16, 19)  # Destination reg
    rn = get_bits(instr, 12, 15)  # Accumulate reg
    rs = get_bits(instr, 8, 11)  # Operand reg
    rm = get_bits(instr, 0, 3)  # Operand reg

    accumulate = get_bit(instr, 21)
    set_cond_codes = get_bit(instr, 20)

    arm_multiply_idle(cpu, cpu.regs.get(rs), True)

    mask = 0xFFFFFFFF

    if accumulate:
        cpu.scheduler.idle(1)
        cpu.regs.set(rd, (cpu.regs.get(rm) * cpu.regs.get(rs) + cpu.regs.get(rn)) & mask)
    else:
        cpu.regs.set(rd, (cpu.regs.get(rm) * cpu.regs.get(rs)) & mask)

    if set_cond_codes:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs.get(rd))
        cpu.regs.cpsr.zero_flag = cpu.regs.get(rd) == 0

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL


def arm_multiply_long(cpu: CPU, instr: int):
    """Execute a Multiply Long instruction"""

    rd_hi = get_bits(instr, 16, 19)  # Upper bits of destination reg
    rd_lo = get_bits(instr, 12, 15)  # Lower bits of destination reg
    rs = get_bits(instr, 8, 11)  # Operand reg
    rm = get_bits(instr, 0, 3)  # Operand reg

    rd_hi_val = cpu.regs.get(rd_hi)
    rd_lo_val = cpu.regs.get(rd_lo)
    rs_val = cpu.regs.get(rs)
    rm_val = cpu.regs.get(rm)

    opcode = get_bits(instr, 21, 22)
    set_cond_codes = get_bit(instr, 20)

    cpu.scheduler.idle(1)

    if opcode == MultiplyLongOpcode.UMULL:
        arm_multiply_idle(cpu, rs_val, False)

        result = rm_val * rs_val

    elif opcode == MultiplyLongOpcode.UMLAL:
        arm_multiply_idle(cpu, rs_val, False)
        cpu.scheduler.idle(1)

        result = (rd_hi_val << 32) | rd_lo_val
        result += rm_val * rs_val

    elif opcode == MultiplyLongOpcode.SMULL:
        arm_multiply_idle(cpu, rs_val, True)

        result = extend_sign_32(rm_val) * extend_sign_32(rs_val)

    elif opcode == MultiplyLongOpcode.SMLAL:
        arm_multiply_idle(cpu, rs_val, True)
        cpu.scheduler.idle(1)

        result = (rd_hi_val << 32) | rd_lo_val
        result += extend_sign_32(rm_val) * extend_sign_32(rs_val)

    # ifndef CYTHON
    else:
        assert False, "Unreachable, opcode must be one of MultiplyLongOpcode"
    # endif

    mask = 0xFFFFFFFF
    cpu.regs.set(rd_lo, result & mask)
    cpu.regs.set(rd_hi, (result >> 32) & mask)

    if set_cond_codes:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs.get(rd_hi))
        cpu.regs.cpsr.zero_flag = cpu.regs.get(rd_hi) == 0 and cpu.regs.get(rd_lo) == 0

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL


def arm_multiply_idle(cpu: CPU, rs: int, signed: bool):
    """
    Idle for the number of cycles it takes to execute a multiply instruction.
    The number of cycles depends on how many MSBs of the Rs operand are
    "all 0" (if unsigned) or "all 0 or all 1" (if signed).
    """

    cycles = 1
    mask = 0xFFFFFF00
    while mask != 0:
        rs &= mask
        if rs == 0 or (signed and rs == mask):
            break
        cycles += 1
        mask <<= 8

    cpu.scheduler.idle(cycles)
