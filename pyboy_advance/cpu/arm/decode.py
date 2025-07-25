from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.arm.alu import arm_alu
from pyboy_advance.cpu.arm.bdt import arm_block_data_transfer
from pyboy_advance.cpu.arm.branch import arm_branch_exchange, arm_branch
from pyboy_advance.cpu.arm.hwdt import arm_halfword_data_transfer
from pyboy_advance.cpu.arm.mul import arm_multiply, arm_multiply_long
from pyboy_advance.cpu.arm.psr import arm_msr, arm_mrs
from pyboy_advance.cpu.arm.sdt import arm_single_data_transfer
from pyboy_advance.cpu.arm.swi import arm_software_interrupt
from pyboy_advance.cpu.arm.swp import arm_single_data_swap

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import InstructionHandler

ARM_PATTERNS: list[tuple[int, int, InstructionHandler]] = [
    # ---------------+-----------------+-----------------------------
    # Mask           | Value           | Handler
    # ---------------+-----------------+-----------------------------
    (0b1111_0000_0000, 0b1111_0000_0000, arm_software_interrupt),
    (0b1110_0000_0000, 0b1010_0000_0000, arm_branch),
    (0b1110_0000_0000, 0b1000_0000_0000, arm_block_data_transfer),
    (0b1100_0000_0000, 0b0100_0000_0000, arm_single_data_transfer),
    (0b1111_1111_1111, 0b0001_0010_0001, arm_branch_exchange),
    (0b1111_1011_1111, 0b0001_0000_1001, arm_single_data_swap),
    (0b1111_1000_1111, 0b0000_1000_1001, arm_multiply_long),
    (0b1111_1100_1111, 0b0000_0000_1001, arm_multiply),
    (0b1110_0000_1001, 0b0000_0000_1001, arm_halfword_data_transfer),
    (0b1101_1011_0000, 0b0001_0000_0000, arm_mrs),
    (0b1101_1011_0000, 0b0001_0010_0000, arm_msr),
    (0b1100_0000_0000, 0b0000_0000_0000, arm_alu),
]

ARM_LUT: list[InstructionHandler | None] = [None] * (2**12)

for lut_index in range(2**12):
    for mask, value, handler in ARM_PATTERNS:
        if (lut_index & mask) == value:
            ARM_LUT[lut_index] = handler
            break


def arm_decode(instr: int) -> InstructionHandler:
    opcode_hash = ((instr >> 16) & 0xFF0) | ((instr >> 4) & 0xF)
    instruction_handler = ARM_LUT[opcode_hash]
    if instruction_handler is None:
        raise ValueError(f"Unknown ARM instruction: {instr:032b}")
    return instruction_handler
