from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_unconditional_branch(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_conditional_branch(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_long_branch_with_link(cpu: CPU, instr: int):
    raise NotImplementedError
