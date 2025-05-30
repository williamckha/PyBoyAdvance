from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_pc_relative_load(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_load_store_register_offset(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_load_store_sign_extended(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_load_store_immediate_offset(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_load_store_halfword(cpu: CPU, instr: int):
    raise NotImplementedError


def thumb_sp_relative_load_store(cpu: CPU, instr: int):
    raise NotImplementedError
