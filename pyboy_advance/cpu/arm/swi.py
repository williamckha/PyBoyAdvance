from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.constants import ExceptionVector

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_software_interrupt(cpu: CPU, instr: int):
    """Execute a Software Interrupt instruction (SWI)"""

    cpu.interrupt(ExceptionVector.SWI)
