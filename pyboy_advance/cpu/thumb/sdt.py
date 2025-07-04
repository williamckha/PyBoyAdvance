from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import get_bits, get_bit, add_uint32_to_uint32

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_pc_relative_load(cpu: CPU, instr: int):
    """
    Execute a THUMB.6 instruction
    (load from memory with PC-relative offset)
    """

    rd = get_bits(instr, 8, 10)  # Source/destination reg

    offset = get_bits(instr, 0, 7) << 2
    address = add_uint32_to_uint32(cpu.regs.pc & ~2, offset)

    cpu.regs[rd] = cpu.memory.read_32_ror(address, MemoryAccess.NON_SEQUENTIAL)
    cpu.scheduler.idle()

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL


def thumb_load_store_register_offset(cpu: CPU, instr: int):
    """
    Execute a THUMB.7 instruction
    (load/store from/into memory with register offset)
    """

    ro = get_bits(instr, 6, 8)  # Offset reg
    rb = get_bits(instr, 3, 5)  # Base reg
    rd = get_bits(instr, 0, 2)  # Source/destination reg

    address = add_uint32_to_uint32(cpu.regs[rb], cpu.regs[ro])

    opcode = get_bits(instr, 10, 11)
    if opcode == 0:  # STR
        cpu.memory.write_32(address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
    elif opcode == 1:  # STRB
        cpu.memory.write_8(address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
    elif opcode == 2:  # LDR
        cpu.regs[rd] = cpu.memory.read_32_ror(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()
    elif opcode == 3:  # LDRB
        cpu.regs[rd] = cpu.memory.read_8(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL


def thumb_load_store_sign_extended(cpu: CPU, instr: int):
    """
    Execute a THUMB.8 instruction
    (load/store sign-extended byte/halfword from/into memory with register offset)
    """

    ro = get_bits(instr, 6, 8)  # Offset reg
    rb = get_bits(instr, 3, 5)  # Base reg
    rd = get_bits(instr, 0, 2)  # Source/destination reg

    address = add_uint32_to_uint32(cpu.regs[rb], cpu.regs[ro])

    opcode = get_bits(instr, 10, 11)
    if opcode == 0:  # STRH
        cpu.memory.write_16(address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
    elif opcode == 1:  # LDSB
        cpu.regs[rd] = cpu.memory.read_8_signed(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()
    elif opcode == 2:  # LDRH
        cpu.regs[rd] = cpu.memory.read_16_ror(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()
    elif opcode == 3:  # LDSH
        cpu.regs[rd] = cpu.memory.read_16_signed(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL


def thumb_load_store_immediate_offset(cpu: CPU, instr: int):
    """
    Execute a THUMB.9 instruction
    (load/store from/into memory with immediate offset)
    """

    rb = get_bits(instr, 3, 5)  # Base reg
    rd = get_bits(instr, 0, 2)  # Source/destination reg

    opcode = get_bits(instr, 11, 12)
    offset = (get_bits(instr, 6, 10) << 2) if opcode in (0, 1) else get_bits(instr, 6, 10)
    address = add_uint32_to_uint32(cpu.regs[rb], offset)

    if opcode == 0:  # STR
        cpu.memory.write_32(address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
    elif opcode == 1:  # LDR
        cpu.regs[rd] = cpu.memory.read_32_ror(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()
    elif opcode == 2:  # STRB
        cpu.memory.write_8(address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
    elif opcode == 3:  # LDRB
        cpu.regs[rd] = cpu.memory.read_8(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL


def thumb_load_store_halfword(cpu: CPU, instr: int):
    """
    Execute a THUMB.10 instruction
    (load/store halfword from/into memory with immediate offset)
    """

    rb = get_bits(instr, 3, 5)  # Base reg
    rd = get_bits(instr, 0, 2)  # Source/destination reg

    offset = get_bits(instr, 6, 10) << 1
    address = add_uint32_to_uint32(cpu.regs[rb], offset)

    opcode = get_bit(instr, 11)
    if opcode:  # LDRH
        cpu.regs[rd] = cpu.memory.read_16_ror(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()
    else:  # STRH
        cpu.memory.write_16(address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL


def thumb_sp_relative_load_store(cpu: CPU, instr: int):
    """
    Execute a THUMB.11 instruction
    (load/store from/into memory with SP-relative offset)
    """

    rd = get_bits(instr, 8, 10)  # Source/destination reg

    offset = get_bits(instr, 0, 7) << 2
    address = add_uint32_to_uint32(cpu.regs.sp, offset)

    opcode = get_bit(instr, 11)
    if opcode:  # LDR
        cpu.regs[rd] = cpu.memory.read_32_ror(address, MemoryAccess.NON_SEQUENTIAL)
        cpu.scheduler.idle()
    else:  # STR
        cpu.memory.write_32(address, cpu.regs[rd], MemoryAccess.NON_SEQUENTIAL)

    cpu.advance_pc_thumb()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL
