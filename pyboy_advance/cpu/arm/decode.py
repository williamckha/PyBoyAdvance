# ifndef CYTHON
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeAlias, TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU

from pyboy_advance.cpu.arm.alu import arm_alu
from pyboy_advance.cpu.arm.bdt import arm_block_data_transfer
from pyboy_advance.cpu.arm.branch import arm_branch_exchange, arm_branch
from pyboy_advance.cpu.arm.hwdt import arm_halfword_data_transfer
from pyboy_advance.cpu.arm.mul import arm_multiply, arm_multiply_long
from pyboy_advance.cpu.arm.psr import arm_msr, arm_mrs
from pyboy_advance.cpu.arm.sdt import arm_single_data_transfer
from pyboy_advance.cpu.arm.swi import arm_software_interrupt
from pyboy_advance.cpu.arm.swp import arm_single_data_swap

# fmt: off
InstrHandler: TypeAlias = Callable[["CPU", int], None]

@dataclass
class InstrPattern:
    mask: int
    value: int
    handler: InstrHandler
# fmt: on
# endif


ARM_PATTERNS: list[InstrPattern] = [
    # ----------+-----------------+-----------------+-----------------------------
    #           | Mask            | Value           | Handler
    # ----------+-----------------+-----------------+-----------------------------
    InstrPattern(0b1111_0000_0000, 0b1111_0000_0000, arm_software_interrupt),
    InstrPattern(0b1110_0000_0000, 0b1010_0000_0000, arm_branch),
    InstrPattern(0b1110_0000_0000, 0b1000_0000_0000, arm_block_data_transfer),
    InstrPattern(0b1100_0000_0000, 0b0100_0000_0000, arm_single_data_transfer),
    InstrPattern(0b1111_1111_1111, 0b0001_0010_0001, arm_branch_exchange),
    InstrPattern(0b1111_1011_1111, 0b0001_0000_1001, arm_single_data_swap),
    InstrPattern(0b1111_1000_1111, 0b0000_1000_1001, arm_multiply_long),
    InstrPattern(0b1111_1100_1111, 0b0000_0000_1001, arm_multiply),
    InstrPattern(0b1110_0000_1001, 0b0000_0000_1001, arm_halfword_data_transfer),
    InstrPattern(0b1101_1011_0000, 0b0001_0000_0000, arm_mrs),
    InstrPattern(0b1101_1011_0000, 0b0001_0010_0000, arm_msr),
    InstrPattern(0b1100_0000_0000, 0b0000_0000_0000, arm_alu),
]


# ifndef CYTHON
ARM_LUT: list[InstrHandler | None] = [None] * (2**12)
# endif


def fill_arm_lut():
    for lut_index in range(2**12):
        for pattern in ARM_PATTERNS:
            if (lut_index & pattern.mask) == pattern.value:
                ARM_LUT[lut_index] = pattern.handler
                break


fill_arm_lut()


def arm_decoder(instr: int) -> InstrHandler:
    opcode_hash = ((instr >> 16) & 0xFF0) | ((instr >> 4) & 0xF)
    instruction_handler = ARM_LUT[opcode_hash]

    # ifndef CYTHON
    if not instruction_handler:
        raise ValueError(f"Unknown ARM instruction: {instr:032b}")
    # endif

    return instruction_handler
