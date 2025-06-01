from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from pyboy_advance.cpu.arm.alu import ALUOpcode, arm_alu
from pyboy_advance.cpu.arm.bdt import arm_block_data_transfer
from pyboy_advance.cpu.arm.branch import arm_branch_exchange, arm_branch
from pyboy_advance.cpu.arm.hwdt import arm_halfword_data_transfer
from pyboy_advance.cpu.arm.mul import arm_multiply, arm_multiply_long
from pyboy_advance.cpu.arm.psr import arm_msr, arm_mrs
from pyboy_advance.cpu.arm.sdt import arm_single_data_transfer
from pyboy_advance.cpu.arm.swi import arm_software_interrupt
from pyboy_advance.cpu.arm.swp import arm_single_data_swap
from pyboy_advance.utils import get_bits, get_bit

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_decode(instr: int) -> Callable[[CPU, int], None]:
    top_bits = get_bits(instr, 26, 27)

    if top_bits == 0b00:
        if get_bits(instr, 4, 25) == 0b00_0001_0010_1111_1111_1111_0001:
            return arm_branch_exchange

        if get_bits(instr, 4, 7) == 0b1001:
            if get_bits(instr, 23, 25) == 0b010 and get_bits(instr, 8, 11) == 0b0000:
                return arm_single_data_swap
            elif get_bits(instr, 22, 25) == 0b0000:
                return arm_multiply
            elif get_bits(instr, 23, 25) == 0b001:
                return arm_multiply_long

        if not get_bit(instr, 25) and get_bit(instr, 7) and get_bit(instr, 4):
            return arm_halfword_data_transfer

        # PSR Transfers are encoded as a subset of Data Processing,
        # with S bit off and opcode field either TST, TEQ, CMP, or CMN
        set_conditions = get_bit(instr, 20)
        alu_opcode = get_bits(instr, 21, 24)
        if not set_conditions and (
            alu_opcode == ALUOpcode.TST
            or alu_opcode == ALUOpcode.TEQ
            or alu_opcode == ALUOpcode.CMP
            or alu_opcode == ALUOpcode.CMN
        ):
            if get_bit(instr, 21):
                return arm_msr
            else:
                return arm_mrs

        # Data Processing is identifiable only by top_bits being 0b00,
        # so it is the last possible instruction we could have at this point
        return arm_alu

    elif top_bits == 0b01:
        return arm_single_data_transfer

    elif top_bits == 0b10:
        if get_bit(instr, 25):
            return arm_branch
        else:
            return arm_block_data_transfer

    elif top_bits == 0b11:
        if get_bits(instr, 24, 25) == 0b11:
            return arm_software_interrupt
        else:
            raise NotImplementedError(f"Coprocessor instruction not implemented: {instr:032b}")

    raise ValueError(f"Unknown ARM instruction: {instr:032b}")
