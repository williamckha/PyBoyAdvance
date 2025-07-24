from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.cpu.constants import CPUMode
from pyboy_advance.cpu.registers import Registers
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import (
    get_bit,
    get_bits,
    add_int32_to_uint32,
    set_bit,
    add_uint32_to_uint32,
)

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


def arm_block_data_transfer(cpu: CPU, instr: int):
    """Execute a Block Data Transfer instruction (LDM, STM)"""

    pre_post_bit = get_bit(instr, 24)
    up_down_bit = get_bit(instr, 23)
    psr_and_force_user_bit = get_bit(instr, 22)
    write_back_bit = get_bit(instr, 21)
    load_store_bit = get_bit(instr, 20)

    base_reg = get_bits(instr, 16, 19)
    reg_list = get_bits(instr, 0, 15)

    reg_list_count = sum(get_bit(reg_list, reg) for reg in range(16))

    # If the reg list is empty, PC is loaded/stored and base is
    # incremented as if all regs were transferred
    if reg_list_count == 0:
        reg_list = set_bit(reg_list, Registers.PC, True)
        reg_list_count = 16

    pc_in_reg_list = get_bit(reg_list, Registers.PC)

    base = cpu.regs[base_reg]

    # Find the final address
    if up_down_bit:
        # Up: add offset to base
        final_address = add_int32_to_uint32(base, reg_list_count * 4)
    else:
        # Down: subtract offset from base
        final_address = add_int32_to_uint32(base, reg_list_count * -4)

        # Move base to the final address and increment from there,
        # instead of decrementing from original base
        base = final_address
        pre_post_bit = not pre_post_bit

    # When S bit (psr_and_force_user_bit) is set and either the instruction is STM
    # or PC is not in the list, this indicates a User Bank Transfer.
    # The reg list refers to registers from the User bank rather than the bank
    # corresponding to the current mode.
    original_mode = cpu.regs.cpsr.mode
    if psr_and_force_user_bit and not (pc_in_reg_list and load_store_bit):
        cpu.switch_mode(CPUMode.USER)

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    first = True
    access_type = MemoryAccess.NON_SEQUENTIAL
    for reg in range(16):
        if get_bit(reg_list, reg):
            if pre_post_bit:  # Pre: add offset before transfer
                base = add_uint32_to_uint32(base, 4)

            if load_store_bit:  # Load
                # Write back before read
                if first and write_back_bit:
                    first = False
                    cpu.regs[base_reg] = final_address

                cpu.regs[reg] = cpu.memory.read_32(base, access_type)
            else:  # Store
                cpu.memory.write_32(base, cpu.regs[reg], access_type)

                # Write back after write
                if first and write_back_bit:
                    first = False
                    cpu.regs[base_reg] = final_address

            if not pre_post_bit:  # Post: add offset after transfer
                base = add_uint32_to_uint32(base, 4)

            access_type = MemoryAccess.SEQUENTIAL

    # When S bit (psr_and_force_user_bit) is set and the instruction is LDM and
    # PC is in the list, this indicates we need to change CPSR=SPSR_<current mode>.
    if pc_in_reg_list and load_store_bit:
        if psr_and_force_user_bit:
            spsr_reg = cpu.regs.spsr.reg
            spsr_mode = cpu.regs.spsr.mode
            cpu.switch_mode(spsr_mode)
            cpu.regs.cpsr.reg = spsr_reg

        # The pipeline also needs to be flushed since PC was changed
        cpu.flush_pipeline()

    # Otherwise, the S bit indicates a User Bank Transfer, so if it's ON then we
    # must have switched into user mode earlier. Hence, we need to switch back
    # into the mode we were in before the transfer.
    elif psr_and_force_user_bit:
        cpu.switch_mode(original_mode)

    if load_store_bit:
        cpu.scheduler.idle()