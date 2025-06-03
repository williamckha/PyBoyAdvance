import logging
from typing import Callable

from pyboy_advance.cpu.arm.decode import arm_decode
from pyboy_advance.cpu.constants import (
    CPUMode,
    CPUState,
    Condition,
    ARM_PC_INCREMENT,
    THUMB_PC_INCREMENT,
    ShiftType,
)
from pyboy_advance.cpu.registers import Registers
from pyboy_advance.cpu.thumb.decode import thumb_decode
from pyboy_advance.memory.memory import MemoryAccess, Memory
from pyboy_advance.utils import (
    get_bits,
    get_bit,
    ror_32,
    add_uint32_to_uint32,
    interpret_signed_32,
)

logger = logging.getLogger(__name__)


class CPU:
    def __init__(self, memory: Memory):
        self.regs = Registers()
        self.regs.cpsr.mode = CPUMode.SYSTEM
        self.regs.spsr.mode = CPUMode.SYSTEM

        self.memory = memory
        self.memory.connect_cpu(self)

        self.pipeline = [0xF0000000, 0xF0000000]
        self.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    def step(self):
        if self.regs.cpsr.state == CPUState.ARM:
            self.arm_step()
        else:
            self.thumb_step()

    def arm_step(self):
        instruction = self.pipeline[0]
        self.pipeline[0] = self.pipeline[1]
        self.pipeline[1] = self.memory.read_32(self.regs.pc, self.next_fetch_access)

        instruction_handler = arm_decode(instruction)

        cond = Condition(get_bits(instruction, 28, 31))
        if self.check_condition(cond):
            logger.debug(
                "Executing <{0:#010x}> {1:032b} {2}".format(
                    (self.regs.pc - 8),
                    instruction,
                    instruction_handler.__name__,
                )
            )

            instruction_handler(self, instruction)
        else:
            # Skip instruction since condition was not met
            logger.debug(
                "Skipping  <{0:#010x}> {1:032b} {2}".format(
                    (self.regs.pc - 8),
                    instruction,
                    instruction_handler.__name__,
                )
            )

            self.arm_advance_pc()
            self.next_fetch_access = MemoryAccess.SEQUENTIAL

    def thumb_step(self):
        instruction = self.pipeline[0]
        self.pipeline[0] = self.pipeline[1]
        self.pipeline[1] = self.memory.read_16(self.regs.pc, self.next_fetch_access)

        instruction_handler = thumb_decode(instruction)

        logger.debug(
            "Executing <{0:#010x}> {1:032b} {2}".format(
                (self.regs.pc - 4),
                instruction,
                instruction_handler.__name__,
            )
        )

        instruction_handler(self, instruction)

    def arm_advance_pc(self):
        self.regs.pc = add_uint32_to_uint32(self.regs.pc, ARM_PC_INCREMENT)

    def thumb_advance_pc(self):
        self.regs.pc = add_uint32_to_uint32(self.regs.pc, THUMB_PC_INCREMENT)

    def flush_pipeline(self):
        if self.regs.cpsr.state == CPUState.ARM:
            self.regs.pc &= ~0b11  # Align PC to 4 byte boundary
            self.pipeline[0] = self.memory.read_32(self.regs.pc, MemoryAccess.NON_SEQUENTIAL)
            self.arm_advance_pc()
            self.pipeline[1] = self.memory.read_32(self.regs.pc, MemoryAccess.SEQUENTIAL)
            self.arm_advance_pc()
        else:
            self.regs.pc &= ~0b1  # Align PC to 2 byte boundary
            self.pipeline[0] = self.memory.read_16(self.regs.pc, MemoryAccess.NON_SEQUENTIAL)
            self.thumb_advance_pc()
            self.pipeline[1] = self.memory.read_16(self.regs.pc, MemoryAccess.SEQUENTIAL)
            self.thumb_advance_pc()
        self.next_fetch_access = MemoryAccess.SEQUENTIAL

    def switch_mode(self, new_mode: CPUMode):
        self.regs.switch_mode(new_mode)

    def check_condition(self, cond: Condition) -> bool:
        cpsr = self.regs.cpsr
        if cond == Condition.EQ:
            return cpsr.zero_flag
        elif cond == Condition.NE:
            return not cpsr.zero_flag
        elif cond == Condition.HS:
            return cpsr.carry_flag
        elif cond == Condition.LO:
            return not cpsr.carry_flag
        elif cond == Condition.MI:
            return cpsr.sign_flag
        elif cond == Condition.PL:
            return not cpsr.sign_flag
        elif cond == Condition.VS:
            return cpsr.overflow_flag
        elif cond == Condition.VC:
            return not cpsr.overflow_flag
        elif cond == Condition.HI:
            return cpsr.carry_flag and not cpsr.zero_flag
        elif cond == Condition.LS:
            return not cpsr.carry_flag or cpsr.zero_flag
        elif cond == Condition.GE:
            return cpsr.sign_flag == cpsr.overflow_flag
        elif cond == Condition.LT:
            return cpsr.sign_flag != cpsr.overflow_flag
        elif cond == Condition.GT:
            return not cpsr.zero_flag and cpsr.sign_flag == cpsr.overflow_flag
        elif cond == Condition.LE:
            return cpsr.zero_flag or cpsr.sign_flag != cpsr.overflow_flag
        elif cond == Condition.AL:
            return True
        elif cond == Condition.NV:
            raise ValueError("Condition NV (never) is reserved")
        else:
            raise ValueError

    def decode_and_compute_shift(self, value: int, shift: int) -> tuple[int, bool]:
        immediate = not get_bit(shift, 0)
        if immediate:
            shift_amount = get_bits(shift, 3, 7)
        else:
            shift_reg = get_bits(shift, 4, 7)
            shift_amount = self.regs[shift_reg] & 0xFF

        shift_type = ShiftType(get_bits(shift, 1, 2))

        return self.compute_shift(value, shift_type, shift_amount, immediate)

    def compute_shift(
        self, value: int, shift_type: ShiftType, shift_amount: int, immediate: bool
    ) -> tuple[int, bool]:
        if not immediate and shift_amount == 0:
            return value, self.regs.cpsr.carry_flag

        result = value
        carry_out = False

        if shift_type == ShiftType.LSL:
            # LSL#0 and Immediate: No shift performed, the C flag is NOT affected.
            # LSL#32 has result zero, carry out equal to bit 0 of value.
            # LSL by more than 32 has result zero, carry out zero.
            if shift_amount == 0:
                carry_out = self.regs.cpsr.carry_flag
            elif shift_amount < 32:
                carry_out = get_bit(value, 32 - shift_amount)
                result = (value << shift_amount) & 0xFFFFFFFF
            elif shift_amount == 32:
                carry_out = get_bit(value, 0)
                result = 0
            else:
                carry_out = False
                result = 0

        elif shift_type == ShiftType.LSR:
            # LSR#0 and Immediate: Interpreted as LSR#32, i.e. result is zero, C becomes bit 31 of value.
            # LSR#32 has result zero, carry out equal to bit 31 of value.
            # LSR by more than 32 has result zero, carry out zero.
            if shift_amount == 0:
                carry_out = get_bit(value, 31)
                result = 0
            elif shift_amount < 32:
                carry_out = get_bit(value, shift_amount - 1)
                result = value >> shift_amount
            elif shift_amount == 32:
                carry_out = get_bit(value, 31)
                result = 0
            else:
                carry_out = False
                result = 0

        elif shift_type == ShiftType.ASR:
            # ASR#0 and Immediate = 0: Interpreted as ASR#32, i.e. result and C are filled by bit 31 of value.
            # ASR by 32 or more has result filled with and carry out equal to bit 31 of value.
            if shift_amount == 0 or shift_amount >= 32:
                carry_out = get_bit(value, 31)
                result = 0xFFFFFFFF if carry_out else 0
            else:
                carry_out = get_bit(value, shift_amount - 1)
                result = (interpret_signed_32(value) >> shift_amount) & 0xFFFFFFFF

        elif shift_type == ShiftType.ROR:
            # ROR by n where n is greater than 32 will give the same result and carry out
            # as ROR by n-32; therefore repeatedly subtract 32 from n until the amount is
            # in the range 1 to 32.
            if shift_amount > 32:
                shift_amount = ((shift_amount - 1) % 32) + 1

            # ROR#0 and Immediate = 0: Interpreted as RRX#1 (RCR), like ROR#1, but bit 31 of result set to old C.
            # ROR#32 has result equal to value, carry out equal to bit 31 of value.
            if shift_amount == 0:
                carry_out = get_bit(value, 0)
                result = (value >> 1) | (self.regs.cpsr.carry_flag << 31)
            else:
                carry_out = get_bit(value, shift_amount - 1)
                result = ror_32(value, get_bits(shift_amount, 0, 4))

        return result, carry_out


InstructionHandler = Callable[[CPU, int], None]
