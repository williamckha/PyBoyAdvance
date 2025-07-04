from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import (
    get_bit,
    get_bits,
    add_int32_to_uint32,
    add_uint32_to_uint32,
)

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def thumb_multiple_load_store(cpu: CPU, instr: int):
    """Execute a THUMB.15 instruction (multiple load/store)"""

    reg_list = get_bits(instr, 0, 7)
    base_reg = get_bits(instr, 8, 10)
    address = cpu.regs[base_reg]

    cpu.advance_pc_thumb()
    cpu.prefetch_access_type = MemoryAccess.NON_SEQUENTIAL

    load = get_bit(instr, 11)  # 0 = STMIA (Store), 1 = LDMIA (Load)

    if reg_list == 0:
        if load:
            cpu.regs.pc = cpu.memory.read_32(cpu.regs[base_reg], MemoryAccess.NON_SEQUENTIAL)
            cpu.flush_pipeline()
        else:
            cpu.memory.write_32(cpu.regs[base_reg], cpu.regs.pc, MemoryAccess.NON_SEQUENTIAL)
        cpu.regs[base_reg] = add_uint32_to_uint32(cpu.regs[base_reg], 0x40)
        return

    count = sum(get_bit(instr, reg) for reg in range(8)) * 4
    access_type = MemoryAccess.NON_SEQUENTIAL

    if load:
        cpu.regs[base_reg] = add_uint32_to_uint32(cpu.regs[base_reg], count)
        cpu.scheduler.idle()

        for reg in range(8):
            if get_bit(reg_list, reg):
                cpu.regs[reg] = cpu.memory.read_32(address, access_type)
                address = add_uint32_to_uint32(address, 4)
                access_type = MemoryAccess.SEQUENTIAL
    else:
        first = True
        for reg in range(8):
            if get_bit(reg_list, reg):
                cpu.memory.write_32(address, cpu.regs[reg], access_type)
                address = add_uint32_to_uint32(address, 4)
                access_type = MemoryAccess.SEQUENTIAL
                if first:
                    cpu.regs[base_reg] = add_uint32_to_uint32(cpu.regs[base_reg], count)
                    first = False


def thumb_push_pop_registers(cpu: CPU, instr: int):
    """Execute a THUMB.14 instruction (push/pop registers to the stack)"""

    reg_list = get_bits(instr, 0, 8)
    opcode = get_bit(instr, 11)

    cpu.advance_pc_thumb()
    cpu.prefetch_access_type = MemoryAccess.NON_SEQUENTIAL

    if opcode:
        thumb_pop_registers(cpu, reg_list)
    else:
        thumb_push_registers(cpu, reg_list)


def thumb_push_registers(cpu: CPU, reg_list: int):
    """
    Push the specified registers to the stack.

    :param cpu:      The CPU executing this instruction.
    :param reg_list: A 9-bit wide bitfield specifying which registers to push.
                     Bits 0-7 correspond to registers R0-R7 and bit 8 corresponds
                     to LR (R14).
    """

    if reg_list == 0:
        cpu.regs.sp = add_int32_to_uint32(cpu.regs.sp, -0x40)
        cpu.memory.write_32(cpu.regs.sp, cpu.regs.pc, MemoryAccess.NON_SEQUENTIAL)
        return

    push_lr = get_bit(reg_list, 8)
    if push_lr:
        cpu.regs.sp = add_int32_to_uint32(cpu.regs.sp, -4)
        cpu.memory.write_32(cpu.regs.sp, cpu.regs.lr, MemoryAccess.NON_SEQUENTIAL)

    for reg in range(7, -1, -1):
        if get_bit(reg_list, reg):
            cpu.regs.sp = add_int32_to_uint32(cpu.regs.sp, -4)
            cpu.memory.write_32(cpu.regs.sp, cpu.regs[reg], MemoryAccess.SEQUENTIAL)


def thumb_pop_registers(cpu: CPU, reg_list: int):
    """
    Pop the specified registers off the stack.

    :param cpu:      The CPU executing this instruction.
    :param reg_list: A 9-bit wide bitfield specifying which registers to pop.
                     Bits 0-7 correspond to registers R0-R7 and bit 8 corresponds
                     to PC (R15).
    """

    if reg_list == 0:
        cpu.regs.pc = cpu.memory.read_32(cpu.regs.sp, MemoryAccess.NON_SEQUENTIAL)
        cpu.regs.sp = add_uint32_to_uint32(cpu.regs.sp, 0x40)
        cpu.flush_pipeline()
        return

    access_type = MemoryAccess.NON_SEQUENTIAL
    for reg in range(8):
        if get_bit(reg_list, reg):
            cpu.regs[reg] = cpu.memory.read_32(cpu.regs.sp, access_type)
            cpu.regs.sp = add_uint32_to_uint32(cpu.regs.sp, 4)
            access_type = MemoryAccess.SEQUENTIAL

    pop_pc = get_bit(reg_list, 8)
    if pop_pc:
        cpu.regs.pc = cpu.memory.read_32(cpu.regs.sp, access_type)
        cpu.regs.sp = add_uint32_to_uint32(cpu.regs.sp, 4)
        cpu.flush_pipeline()

    cpu.scheduler.idle()