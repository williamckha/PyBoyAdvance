from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.constants import ExceptionVector

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_software_interrupt(cpu: CPU, instr: int):
    """Execute a THUMB.17 instruction (software interrupt)"""

    cpu.interrupt(ExceptionVector.SWI)
