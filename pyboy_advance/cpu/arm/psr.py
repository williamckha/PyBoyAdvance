from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.constants import CPUMode
from pyboy_advance.cpu.registers import ProgramStatusRegister
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import get_bits, get_bit, ror_32

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_mrs(cpu: CPU, instr: int):
    """
    Execute an MRS instruction
    (transfer PSR contents to general-purpose register)
    """

    # Destination reg
    rd = get_bits(instr, 12, 15)

    # Source PSR; 0 = CPSR, 1 = SPSR_<current_mode>
    psr = get_bit(instr, 22)
    cpu.regs[rd] = cpu.regs.spsr.reg if psr else cpu.regs.cpsr.reg

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL


def arm_msr(cpu: CPU, instr: int):
    """
    Execute an MSR instruction
    (transfer general-purpose register contents or immediate value to PSR)
    """

    immediate = get_bit(instr, 25)
    if immediate:
        value = get_bits(instr, 0, 7)
        ror_amount = get_bits(instr, 8, 11) * 2
        value = ror_32(value, ror_amount)
    else:
        value = cpu.regs[get_bits(instr, 0, 3)]

    write_to_flags_field = get_bit(instr, 19)
    write_to_status_field = get_bit(instr, 18)
    write_to_extension_field = get_bit(instr, 17)
    write_to_control_field = get_bit(instr, 16)

    mask = 0
    mask |= 0xFF000000 if write_to_flags_field else 0
    mask |= 0x00FF0000 if write_to_status_field else 0
    mask |= 0x0000FF00 if write_to_extension_field else 0
    mask |= 0x000000FF if write_to_control_field else 0

    # Destination PSR; 0 = CPSR, 1 = SPSR_<current_mode>
    psr = get_bit(instr, 22)

    if psr:
        cpu.regs.spsr.reg = (cpu.regs.spsr.reg & ~mask) | (value & mask)
    else:
        # In user mode, only the condition flags can be changed
        if cpu.regs.cpsr.mode == CPUMode.USER:
            mask &= 0xFF000000

        new_cpsr = ProgramStatusRegister((cpu.regs.cpsr.reg & ~mask) | (value & mask))
        cpu.switch_mode(new_cpsr.mode)
        cpu.regs.cpsr.reg = new_cpsr.reg

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.SEQUENTIAL
