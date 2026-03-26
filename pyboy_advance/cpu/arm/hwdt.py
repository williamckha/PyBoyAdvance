# ifndef CYTHON
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU

from pyboy_advance.cpu.arm.constants import DataTransferOpcode
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import get_bits, get_bit, add_32
# endif


def arm_halfword_data_transfer(cpu: CPU, instr: int):
    """Execute a Halfword Data Transfer instruction (LDRH, STRH, etc.)"""

    rn = get_bits(instr, 16, 19)  # Base reg
    rd = get_bits(instr, 12, 15)  # Source/dest reg

    pre_post_bit = get_bit(instr, 24)
    up_down_bit = get_bit(instr, 23)
    immediate_bit = get_bit(instr, 22)
    write_back_bit = get_bit(instr, 21)
    load_store_bit = get_bit(instr, 20)

    offset = (
        (get_bits(instr, 8, 11) << 4) | get_bits(instr, 0, 3)
        if immediate_bit
        else cpu.regs.get(get_bits(instr, 0, 3))
    )

    base = cpu.regs.get(rn)
    address = add_32(base, offset if up_down_bit else -offset)
    effective_address = address if pre_post_bit else base

    cpu.advance_pc_arm()
    cpu.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    opcode = get_bits(instr, 5, 6)

    if load_store_bit:  # Load
        # When post-indexing, write back is always enabled
        # When pre-indexing, write back is optional (controlled by W bit)
        if not pre_post_bit or write_back_bit:
            cpu.regs.set(rn, address)

        if opcode == DataTransferOpcode.LDRH:
            cpu.regs.set(rd, cpu.memory.read_16_ror(effective_address, MemoryAccess.NON_SEQUENTIAL))
        elif opcode == DataTransferOpcode.LDRSB:
            cpu.regs.set(
                rd, cpu.memory.read_8_signed(effective_address, MemoryAccess.NON_SEQUENTIAL)
            )
        elif opcode == DataTransferOpcode.LDRSH:
            cpu.regs.set(
                rd, cpu.memory.read_16_signed(effective_address, MemoryAccess.NON_SEQUENTIAL)
            )

        cpu.scheduler.idle(1)

        if rd == cpu.regs.PC:
            cpu.flush_pipeline()

    else:  # Store
        if opcode == DataTransferOpcode.STRH:
            cpu.memory.write_16(effective_address, cpu.regs.get(rd), MemoryAccess.NON_SEQUENTIAL)
        elif opcode == DataTransferOpcode.LDRD:
            pass  # LDRD not implemented on ARM7
        elif opcode == DataTransferOpcode.STRD:
            pass  # STRD not implemented on ARM7

        # When post-indexing, write back is always enabled
        # When pre-indexing, write back is optional (controlled by W bit)
        if not pre_post_bit or write_back_bit:
            cpu.regs.set(rn, address)
