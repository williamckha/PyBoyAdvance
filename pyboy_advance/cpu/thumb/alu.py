from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pyboy_advance.cpu.arm.alu import (
    arm_alu_sub,
    arm_alu_add,
    arm_alu_mov,
    arm_alu_adc,
    arm_alu_sbc,
    arm_alu_tst,
    arm_alu_cmp,
    arm_alu_cmn,
    arm_alu_orr,
    arm_alu_bic,
    arm_alu_mvn,
    arm_alu_and,
    arm_alu_eor,
)
from pyboy_advance.cpu.arm.mul import arm_multiply_idle
from pyboy_advance.cpu.constants import CPUState, ShiftType
from pyboy_advance.cpu.registers import Registers
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import (
    get_bits,
    get_bit,
    sign_32,
    add_uint32_to_uint32,
    add_int32_to_uint32,
)

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


class ThumbALUOpcode(IntEnum):
    AND = 0x0
    EOR = 0x1
    LSL = 0x2
    LSR = 0x3
    ASR = 0x4
    ADC = 0x5
    SBC = 0x6
    ROR = 0x7
    TST = 0x8
    NEG = 0x9
    CMP = 0xA
    CMN = 0xB
    ORR = 0xC
    MUL = 0xD
    BIC = 0xE
    MVN = 0xF


def thumb_move_shifted_register(cpu: CPU, instr: int):
    """Execute a THUMB.1 instruction (move shifted register)"""

    rs = get_bits(instr, 3, 5)  # Source reg
    rd = get_bits(instr, 0, 2)  # Destination reg

    opcode = ShiftType(get_bits(instr, 11, 12))
    offset = get_bits(instr, 6, 10)

    result, carry = cpu.compute_shift(cpu.regs[rs], opcode, offset, immediate=True)

    cpu.regs[rd] = result
    cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
    cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
    cpu.regs.cpsr.carry_flag = carry

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_add_subtract(cpu: CPU, instr: int):
    """Execute a THUMB.2 instruction (add/subtract)"""

    rs = get_bits(instr, 3, 5)  # Source reg
    rd = get_bits(instr, 0, 2)  # Destination reg

    opcode = get_bits(instr, 9, 10)
    immediate_bit = get_bit(instr, 10)

    op1 = cpu.regs[rs]
    op2 = get_bits(instr, 6, 8) if immediate_bit else cpu.regs[get_bits(instr, 6, 8)]

    if opcode == 0:  # ADD (Register)
        arm_alu_add(cpu, op1, op2, rd, set_cond_codes=True)
    elif opcode == 1:  # SUB (Register)
        arm_alu_sub(cpu, op1, op2, rd, set_cond_codes=True)
    elif opcode == 2:  # ADD (Immediate)
        arm_alu_add(cpu, op1, op2, rd, set_cond_codes=True)
    elif opcode == 3:  # SUB (Immediate)
        arm_alu_sub(cpu, op1, op2, rd, set_cond_codes=True)

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_move_compare_add_subtract(cpu: CPU, instr: int):
    """Execute a THUMB.3 instruction (move/compare/add/subtract immediate)"""

    rd = get_bits(instr, 8, 10)  # Destination reg

    opcode = get_bits(instr, 11, 12)
    value = get_bits(instr, 0, 7)

    if opcode == 0:  # MOV
        arm_alu_mov(cpu, value, rd, set_cond_codes=True, shift_carry=cpu.regs.cpsr.carry_flag)
    elif opcode == 1:  # CMP
        arm_alu_cmp(cpu, cpu.regs[rd], value)
    elif opcode == 2:  # ADD
        arm_alu_add(cpu, cpu.regs[rd], value, rd, set_cond_codes=True)
    elif opcode == 3:  # SUB
        arm_alu_sub(cpu, cpu.regs[rd], value, rd, set_cond_codes=True)

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_alu(cpu: CPU, instr: int):
    """Execute a THUMB.4 instruction (miscellaneous ALU operations)"""

    rs = get_bits(instr, 3, 5)
    rd = get_bits(instr, 0, 2)

    op1 = cpu.regs[rd]
    op2 = cpu.regs[rs]

    def execute_shift(shift_type: ShiftType):
        shift = op2 & 0xFF
        result, carry = cpu.compute_shift(op1, shift_type, shift, immediate=False)

        cpu.regs[rd] = result
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
        cpu.regs.cpsr.carry_flag = carry

        cpu.scheduler.idle()

    opcode = get_bits(instr, 6, 9)
    if opcode == ThumbALUOpcode.AND:
        arm_alu_and(cpu, op1, op2, rd, set_cond_codes=True, shift_carry=cpu.regs.cpsr.carry_flag)
    elif opcode == ThumbALUOpcode.EOR:
        arm_alu_eor(cpu, op1, op2, rd, set_cond_codes=True, shift_carry=cpu.regs.cpsr.carry_flag)
    elif opcode == ThumbALUOpcode.LSL:
        execute_shift(ShiftType.LSL)
    elif opcode == ThumbALUOpcode.LSR:
        execute_shift(ShiftType.LSR)
    elif opcode == ThumbALUOpcode.ASR:
        execute_shift(ShiftType.ASR)
    elif opcode == ThumbALUOpcode.ADC:
        arm_alu_adc(cpu, op1, op2, rd, set_cond_codes=True)
    elif opcode == ThumbALUOpcode.SBC:
        arm_alu_sbc(cpu, op1, op2, rd, set_cond_codes=True)
    elif opcode == ThumbALUOpcode.ROR:
        execute_shift(ShiftType.ROR)
    elif opcode == ThumbALUOpcode.TST:
        arm_alu_tst(cpu, op1, op2, shift_carry=cpu.regs.cpsr.carry_flag)
    elif opcode == ThumbALUOpcode.NEG:
        arm_alu_sub(cpu, 0, op2, rd, set_cond_codes=True)
    elif opcode == ThumbALUOpcode.CMP:
        arm_alu_cmp(cpu, op1, op2)
    elif opcode == ThumbALUOpcode.CMN:
        arm_alu_cmn(cpu, op1, op2)
    elif opcode == ThumbALUOpcode.ORR:
        arm_alu_orr(cpu, op1, op2, rd, set_cond_codes=True, shift_carry=cpu.regs.cpsr.carry_flag)
    elif opcode == ThumbALUOpcode.MUL:
        cpu.regs[rd] = (op1 * op2) & 0xFFFFFFFF
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
        arm_multiply_idle(cpu, op1, signed=True)
    elif opcode == ThumbALUOpcode.BIC:
        arm_alu_bic(cpu, op1, op2, rd, set_cond_codes=True, shift_carry=cpu.regs.cpsr.carry_flag)
    elif opcode == ThumbALUOpcode.MVN:
        arm_alu_mvn(cpu, op2, rd, set_cond_codes=True, shift_carry=cpu.regs.cpsr.carry_flag)

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_high_reg_branch_exchange(cpu: CPU, instr: int):
    """Execute a THUMB.5 instruction (high register operations or branch exchange)"""

    rs = (get_bit(instr, 6) << 3) | get_bits(instr, 3, 5)
    rd = (get_bit(instr, 7) << 3) | get_bits(instr, 0, 2)

    opcode = get_bits(instr, 8, 9)

    if opcode == 0:  # ADD
        cpu.regs[rd] = add_uint32_to_uint32(cpu.regs[rd], cpu.regs[rs])
        if rd == Registers.PC:
            cpu.flush_pipeline()
            return

    elif opcode == 1:  # CMP
        arm_alu_cmp(cpu, cpu.regs[rd], cpu.regs[rs])

    elif opcode == 2:  # MOV
        cpu.regs[rd] = cpu.regs[rs]
        if rd == Registers.PC:
            cpu.flush_pipeline()
            return

    elif opcode == 3:  # BX
        address = cpu.regs[rs]

        # Mask out the last bit indicating whether to switch to ARM mode
        cpu.regs.pc = address & ~1
        cpu.regs.cpsr.state = CPUState(get_bit(address, 0))

        cpu.flush_pipeline()
        return

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_get_address(cpu: CPU, instr: int):
    """Execute a THUMB.12 instruction (get address relative to SP/PC)"""

    opcode = get_bit(instr, 11)
    rd = get_bits(instr, 8, 10)
    offset = get_bits(instr, 0, 7) * 4

    if opcode:
        # Load from SP
        cpu.regs[rd] = add_uint32_to_uint32(cpu.regs.sp, offset)
    else:
        # Load from PC
        cpu.regs[rd] = add_uint32_to_uint32(cpu.regs.pc & ~2, offset)

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def thumb_add_offset_to_stack_pointer(cpu: CPU, instr: int):
    """Execute a THUMB.13 instruction (add offset to SP)"""
    
    sign = -1 if get_bit(instr, 7) else 1
    offset = sign * get_bits(instr, 0, 6) * 4

    cpu.regs.sp = add_int32_to_uint32(cpu.regs.sp, offset)

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL
