from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_multiple_load_store(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_push_pop_registers(cpu: CPU, instr: int):
    raise NotImplementedError
