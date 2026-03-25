# ifndef CYTHON
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU

from pyboy_advance.cpu.arm.constants import ALUOpcode
from pyboy_advance.utils import get_bits, get_bit, ror_32, sign_32, bint
# endif


def arm_alu(cpu: CPU, instr: int):
    """Execute a Data Processing (ALU) instruction (AND, EOR, ADD, SUB, MOV, etc.)"""

    rn = get_bits(instr, 16, 19)
    rd = get_bits(instr, 12, 15)

    shift_carry = cpu.regs.cpsr.carry_flag

    set_cond_codes = get_bit(instr, 20)
    immediate = get_bit(instr, 25)

    early_advance_pc = False

    if immediate:  # Immediate value as 2nd operand
        op1 = cpu.regs.get(rn)
        op2 = get_bits(instr, 0, 7)
        ror_amount = get_bits(instr, 8, 11) * 2

        if ror_amount > 0:
            shift_carry = get_bit(op2, ror_amount - 1)
            op2 = ror_32(op2, ror_amount)

    else:  # Register value as 2nd operand
        rm = get_bits(instr, 0, 3)
        shift = get_bits(instr, 4, 11)

        # When using PC as an operand, the returned value depends on the instruction.
        # If shifting by register (shift[0] = 1) and using a register value as op2,
        # then the operand should be PC + 12.
        if get_bit(shift, 0):
            # Advance PC by 4 so that cpu.regs.pc returns PC + 12
            cpu.advance_pc_arm()
            early_advance_pc = True
            cpu.scheduler.idle()
        else:
            # Otherwise, the operand should be PC + 8
            # (which is what cpu.regs.pc returns normally).
            pass

        op1 = cpu.regs.get(rn)
        op2, shift_carry = cpu.decode_and_compute_shift(cpu.regs.get(rm), shift)

    opcode = get_bits(instr, 21, 24)
    if opcode == ALUOpcode.AND:
        arm_alu_and(cpu, op1, op2, rd, set_cond_codes, shift_carry)
    elif opcode == ALUOpcode.EOR:
        arm_alu_eor(cpu, op1, op2, rd, set_cond_codes, shift_carry)
    elif opcode == ALUOpcode.SUB:
        arm_alu_sub(cpu, op1, op2, rd, set_cond_codes)
    elif opcode == ALUOpcode.RSB:
        arm_alu_rsb(cpu, op1, op2, rd, set_cond_codes)
    elif opcode == ALUOpcode.ADD:
        arm_alu_add(cpu, op1, op2, rd, set_cond_codes)
    elif opcode == ALUOpcode.ADC:
        arm_alu_adc(cpu, op1, op2, rd, set_cond_codes)
    elif opcode == ALUOpcode.SBC:
        arm_alu_sbc(cpu, op1, op2, rd, set_cond_codes)
    elif opcode == ALUOpcode.RSC:
        arm_alu_rsc(cpu, op1, op2, rd, set_cond_codes)
    elif opcode == ALUOpcode.TST:
        arm_alu_tst(cpu, op1, op2, shift_carry)
    elif opcode == ALUOpcode.TEQ:
        arm_alu_teq(cpu, op1, op2, shift_carry)
    elif opcode == ALUOpcode.CMP:
        arm_alu_cmp(cpu, op1, op2)
    elif opcode == ALUOpcode.CMN:
        arm_alu_cmn(cpu, op1, op2)
    elif opcode == ALUOpcode.ORR:
        arm_alu_orr(cpu, op1, op2, rd, set_cond_codes, shift_carry)
    elif opcode == ALUOpcode.MOV:
        arm_alu_mov(cpu, op2, rd, set_cond_codes, shift_carry)
    elif opcode == ALUOpcode.BIC:
        arm_alu_bic(cpu, op1, op2, rd, set_cond_codes, shift_carry)
    elif opcode == ALUOpcode.MVN:
        arm_alu_mvn(cpu, op2, rd, set_cond_codes, shift_carry)

    # When S bit = 1 (set_cond_codes) and Rd = PC, the result of operation is stored in PC
    # and SPSR of the current mode is moved to CPSR
    if rd == cpu.regs.PC:
        if set_cond_codes:
            new_cpsr_reg = cpu.regs.spsr.reg
            new_cpsr_mode = cpu.regs.spsr.mode
            cpu.switch_mode(new_cpsr_mode)
            cpu.regs.cpsr.reg = new_cpsr_reg

        # Read only operations do not flush the pipeline
        if opcode not in [ALUOpcode.TST, ALUOpcode.TEQ, ALUOpcode.CMP, ALUOpcode.CMN]:
            cpu.flush_pipeline()

    elif not early_advance_pc:
        cpu.advance_pc_arm()


def arm_alu_and(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint, shift_carry: bint):
    cpu.regs.set(rd, arm_alu_and_impl(cpu, op1, op2, rd, set_cond_codes, shift_carry))


def arm_alu_and_impl(
    cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint, shift_carry: bint
) -> int:
    result = op1 & op2
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(result)
        cpu.regs.cpsr.zero_flag = result == 0
        cpu.regs.cpsr.carry_flag = shift_carry
    return result


def arm_alu_eor(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint, shift_carry: bint):
    cpu.regs.set(rd, arm_alu_eor_impl(cpu, op1, op2, rd, set_cond_codes, shift_carry))


def arm_alu_eor_impl(
    cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint, shift_carry: bint
) -> int:
    result = op1 ^ op2
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(result)
        cpu.regs.cpsr.zero_flag = result == 0
        cpu.regs.cpsr.carry_flag = shift_carry
    return result


def arm_alu_sub(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint):
    cpu.regs.set(rd, arm_alu_sub_impl(cpu, op1, op2, rd, set_cond_codes))


def arm_alu_sub_impl(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint) -> int:
    mask = 0xFFFFFFFF
    result = op1 - op2
    truncated_result = result & mask
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(truncated_result)
        cpu.regs.cpsr.zero_flag = truncated_result == 0
        cpu.regs.cpsr.carry_flag = op1 >= op2  # Carry = no borrow
        cpu.regs.cpsr.overflow_flag = sign_32((op1 ^ op2) & (op1 ^ truncated_result))
    return truncated_result


def arm_alu_rsb(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint):
    arm_alu_sub(cpu, op2, op1, rd, set_cond_codes)


def arm_alu_add(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint):
    cpu.regs.set(rd, arm_alu_add_impl(cpu, op1, op2, rd, set_cond_codes))


def arm_alu_add_impl(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint) -> int:
    mask = 0xFFFFFFFF
    result = op1 + op2
    truncated_result = result & mask
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(truncated_result)
        cpu.regs.cpsr.zero_flag = truncated_result == 0
        cpu.regs.cpsr.carry_flag = result > mask
        cpu.regs.cpsr.overflow_flag = sign_32(~(op1 ^ op2) & (op2 ^ truncated_result))
    return truncated_result


def arm_alu_adc(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint):
    mask = 0xFFFFFFFF
    carry = cpu.regs.cpsr.carry_flag
    result = op1 + op2 + carry
    cpu.regs.set(rd, result & mask)
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs.get(rd))
        cpu.regs.cpsr.zero_flag = cpu.regs.get(rd) == 0
        cpu.regs.cpsr.carry_flag = result > mask
        cpu.regs.cpsr.overflow_flag = sign_32(~(op1 ^ op2) & (op2 ^ cpu.regs.get(rd)))


def arm_alu_sbc(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint):
    mask = 0xFFFFFFFF
    borrow = 1 - cpu.regs.cpsr.carry_flag  # Carry = no borrow, so subtract 0
    result = op1 - op2 - borrow
    cpu.regs.set(rd, result & mask)
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs.get(rd))
        cpu.regs.cpsr.zero_flag = cpu.regs.get(rd) == 0
        cpu.regs.cpsr.carry_flag = op1 >= (op2 + borrow)
        cpu.regs.cpsr.overflow_flag = sign_32((op1 ^ op2) & (op1 ^ cpu.regs.get(rd)))


def arm_alu_rsc(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint):
    arm_alu_sbc(cpu, op2, op1, rd, set_cond_codes)


def arm_alu_tst(cpu: CPU, op1: int, op2: int, shift_carry: bint):
    arm_alu_and_impl(cpu, op1, op2, 0, True, shift_carry)


def arm_alu_teq(cpu: CPU, op1: int, op2: int, shift_carry: bint):
    arm_alu_eor_impl(cpu, op1, op2, 0, True, shift_carry)


def arm_alu_cmp(cpu: CPU, op1: int, op2: int):
    arm_alu_sub_impl(cpu, op1, op2, 0, True)


def arm_alu_cmn(cpu: CPU, op1: int, op2: int):
    arm_alu_add_impl(cpu, op1, op2, 0, True)


def arm_alu_orr(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint, shift_carry: bint):
    cpu.regs.set(rd, op1 | op2)
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs.get(rd))
        cpu.regs.cpsr.zero_flag = cpu.regs.get(rd) == 0
        cpu.regs.cpsr.carry_flag = shift_carry


def arm_alu_mov(cpu: CPU, op2: int, rd: int, set_cond_codes: bint, shift_carry: bint):
    cpu.regs.set(rd, op2)
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs.get(rd))
        cpu.regs.cpsr.zero_flag = cpu.regs.get(rd) == 0
        cpu.regs.cpsr.carry_flag = shift_carry


def arm_alu_bic(cpu: CPU, op1: int, op2: int, rd: int, set_cond_codes: bint, shift_carry: bint):
    cpu.regs.set(rd, op1 & ~op2)
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs.get(rd))
        cpu.regs.cpsr.zero_flag = cpu.regs.get(rd) == 0
        cpu.regs.cpsr.carry_flag = shift_carry


def arm_alu_mvn(cpu: CPU, op2: int, rd: int, set_cond_codes: bint, shift_carry: bint):
    mask = 0xFFFFFFFF
    cpu.regs.set(rd, ~op2 & mask)
    if set_cond_codes and rd != cpu.regs.PC:
        cpu.regs.cpsr.sign_flag = sign_32(cpu.regs.get(rd))
        cpu.regs.cpsr.zero_flag = cpu.regs.get(rd) == 0
        cpu.regs.cpsr.carry_flag = shift_carry
