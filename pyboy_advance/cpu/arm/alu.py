from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pyboy_advance.cpu.registers import Registers
from pyboy_advance.utils import get_bits, get_bit, ror_32, sign_32

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


class ALUOpcode(IntEnum):
    AND = 0x0
    EOR = 0x1
    SUB = 0x2
    RSB = 0x3
    ADD = 0x4
    ADC = 0x5
    SBC = 0x6
    RSC = 0x7
    TST = 0x8
    TEQ = 0x9
    CMP = 0xA
    CMN = 0xB
    ORR = 0xC
    MOV = 0xD
    BIC = 0xE
    MVN = 0xF


def arm_alu(cpu: CPU, instr: int):
    """Execute a Data Processing (ALU) instruction (AND, EOR, ADD, SUB, MOV, etc.)"""

    rn = get_bits(instr, 16, 19)
    rd = get_bits(instr, 12, 15)

    op1 = cpu.regs[rn]
    op2: int
    shift_carry = cpu.regs.cpsr.carry_flag

    set_cond = get_bit(instr, 20)
    immediate = get_bit(instr, 25)

    if immediate:
        # Immediate value as 2nd operand
        op2 = get_bits(instr, 0, 7)
        ror_amount = get_bits(instr, 8, 11) * 2
        if ror_amount > 0:
            shift_carry = get_bit(op2 >> (ror_amount - 1), 0)
            op2 = ror_32(op2, ror_amount)
    else:
        # Register value as 2nd operand
        rm = get_bits(instr, 0, 3)
        shift = get_bits(instr, 4, 11)
        op2, shift_carry = cpu.compute_shift(cpu.regs[rm], shift)

    opcode = ALUOpcode(get_bits(instr, 21, 24))
    match opcode:
        case ALUOpcode.AND:
            arm_alu_and(cpu, op1, op2, rd, set_cond, shift_carry)
        case ALUOpcode.EOR:
            arm_alu_eor(cpu, op1, op2, rd, set_cond, shift_carry)
        case ALUOpcode.SUB:
            arm_alu_sub(cpu, op1, op2, rd, set_cond)
        case ALUOpcode.RSB:
            arm_alu_rsb(cpu, op1, op2, rd, set_cond)
        case ALUOpcode.ADD:
            arm_alu_add(cpu, op1, op2, rd, set_cond)
        case ALUOpcode.ADC:
            arm_alu_adc(cpu, op1, op2, rd, set_cond)
        case ALUOpcode.SBC:
            arm_alu_sbc(cpu, op1, op2, rd, set_cond)
        case ALUOpcode.RSC:
            arm_alu_rsc(cpu, op1, op2, rd, set_cond)
        case ALUOpcode.TST:
            arm_alu_tst(cpu, op1, op2, shift_carry)
        case ALUOpcode.TEQ:
            arm_alu_teq(cpu, op1, op2, shift_carry)
        case ALUOpcode.CMP:
            arm_alu_cmp(cpu, op1, op2)
        case ALUOpcode.CMN:
            arm_alu_cmn(cpu, op1, op2)
        case ALUOpcode.ORR:
            arm_alu_orr(cpu, op1, op2, rd, set_cond, shift_carry)
        case ALUOpcode.MOV:
            arm_alu_mov(cpu, op2, rd, set_cond, shift_carry)
        case ALUOpcode.BIC:
            arm_alu_bic(cpu, op1, op2, rd, set_cond, shift_carry)
        case ALUOpcode.MVN:
            arm_alu_mvn(cpu, op2, rd, set_cond, shift_carry)

    # When S bit = 1 (set_cond) and Rd = PC, the result of operation is stored in PC
    # and SPSR of the current mode is moved to CPSR
    if rd == Registers.PC:
        if set_cond:
            new_cpsr_reg = cpu.regs.spsr.reg
            new_cpsr_mode = cpu.regs.spsr.mode
            cpu.switch_mode(new_cpsr_mode)
            cpu.regs.cpsr.reg = new_cpsr_reg

        # Read only operations do not flush the pipeline
        if opcode not in [ALUOpcode.TST, ALUOpcode.TEQ, ALUOpcode.CMP, ALUOpcode.CMN]:
            cpu.flush_pipeline()
    else:
        cpu.arm_advance_pc()


def arm_alu_and(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool, shift_carry: bool):
    cpu.regs[rd] = arm_alu_and_impl(cpu, op1, op2, rd, set_cond, shift_carry)


def arm_alu_and_impl(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool, shift_carry: bool) -> int:
    result = op1 & op2
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(result)
        cpu.regs.cpsr.zero_flag = result == 0
        cpu.regs.cpsr.carry_flag = shift_carry
    return result


def arm_alu_eor(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool, shift_carry: bool):
    cpu.regs[rd] = arm_alu_eor_impl(cpu, op1, op2, rd, set_cond, shift_carry)


def arm_alu_eor_impl(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool, shift_carry: bool) -> int:
    result = op1 ^ op2
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(result)
        cpu.regs.cpsr.zero_flag = result == 0
        cpu.regs.cpsr.carry_flag = shift_carry
    return result


def arm_alu_sub(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool):
    cpu.regs[rd] = arm_alu_sub_impl(cpu, op1, op2, rd, set_cond)


def arm_alu_sub_impl(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool) -> int:
    result = op1 - op2
    truncated_result = result & 0xFFFFFFFF
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(truncated_result)
        cpu.regs.cpsr.zero_flag = truncated_result == 0
        cpu.regs.cpsr.carry_flag = op1 >= op2  # Carry = no borrow
        cpu.regs.cpsr.overflow_flag = sign_32((op1 ^ op2) & (op1 ^ truncated_result))
    return truncated_result


def arm_alu_rsb(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool):
    arm_alu_sub(cpu, op2, op1, rd, set_cond)


def arm_alu_add(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool):
    cpu.regs[rd] = arm_alu_add_impl(cpu, op1, op2, rd, set_cond)


def arm_alu_add_impl(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool) -> int:
    result = op1 + op2
    truncated_result = result & 0xFFFFFFFF
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(truncated_result)
        cpu.regs.cpsr.zero_flag = truncated_result == 0
        cpu.regs.cpsr.carry_flag = result > 0xFFFFFFFF
        cpu.regs.cpsr.overflow_flag = sign_32(~(op1 ^ op2) & (op2 ^ truncated_result))
    return truncated_result


def arm_alu_adc(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool):
    carry = cpu.regs.cpsr.carry_flag
    result = op1 + op2 + carry
    cpu.regs[rd] = result & 0xFFFFFFFF
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
        cpu.regs.cpsr.carry_flag = result > 0xFFFFFFFF
        cpu.regs.cpsr.overflow_flag = sign_32(~(op1 ^ op2) & (op2 ^ cpu.regs[rd]))


def arm_alu_sbc(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool):
    borrow = 1 - cpu.regs.cpsr.carry_flag  # Carry = no borrow, so subtract 0
    result = op1 - op2 - borrow
    cpu.regs[rd] = result & 0xFFFFFFFF
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
        cpu.regs.cpsr.carry_flag = op1 >= (op2 + borrow)
        cpu.regs.cpsr.overflow_flag = sign_32((op1 ^ op2) & (op1 ^ cpu.regs[rd]))


def arm_alu_rsc(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool):
    arm_alu_sbc(cpu, op2, op1, rd, set_cond)


def arm_alu_tst(cpu: CPU, op1: int, op2: int, shift_carry: bool):
    arm_alu_and_impl(cpu, op1, op2, 0, True, shift_carry)


def arm_alu_teq(cpu: CPU, op1: int, op2: int, shift_carry: bool):
    arm_alu_eor_impl(cpu, op1, op2, 0, True, shift_carry)


def arm_alu_cmp(cpu: CPU, op1: int, op2: int):
    arm_alu_sub_impl(cpu, op1, op2, 0, True)


def arm_alu_cmn(cpu: CPU, op1: int, op2: int):
    arm_alu_add_impl(cpu, op1, op2, 0, True)


def arm_alu_orr(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool, shift_carry: bool):
    cpu.regs[rd] = op1 | op2
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
        cpu.regs.cpsr.carry_flag = shift_carry


def arm_alu_mov(cpu: CPU, op2: int, rd: int, set_cond: bool, shift_carry: bool):
    cpu.regs[rd] = op2
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
        cpu.regs.cpsr.carry_flag = shift_carry


def arm_alu_bic(cpu: CPU, op1: int, op2: int, rd: int, set_cond: bool, shift_carry: bool):
    cpu.regs[rd] = op1 & ~op2
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
        cpu.regs.cpsr.carry_flag = shift_carry


def arm_alu_mvn(cpu: CPU, op2: int, rd: int, set_cond: bool, shift_carry: bool):
    cpu.regs[rd] = ~op2
    if set_cond and rd != Registers.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs[rd])
        cpu.regs.cpsr.zero_flag = cpu.regs[rd] == 0
        cpu.regs.cpsr.carry_flag = shift_carry
