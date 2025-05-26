from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_software_interrupt(cpu: CPU, instr: int):
    return
