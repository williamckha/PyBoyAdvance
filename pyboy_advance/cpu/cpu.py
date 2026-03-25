import logging

# ifndef CYTHON
from pyboy_advance.cpu.arm.decode import arm_decode
from pyboy_advance.cpu.constants import (
    CPUMode,
    CPUState,
    Condition,
    ARM_PC_INCREMENT,
    THUMB_PC_INCREMENT,
    ShiftType,
    ExceptionVector,
)
from pyboy_advance.cpu.registers import Registers
from pyboy_advance.cpu.thumb.decode import thumb_decode
from pyboy_advance.memory.memory import Memory
from pyboy_advance.memory.constants import MemoryAccess
from pyboy_advance.utils import (
    get_bits,
    get_bit,
    ror_32,
    add_32,
    extend_sign_32,
    bint,
)
# endif

from pyboy_advance.interrupt_controller import PowerDownMode
from pyboy_advance.scheduler import Scheduler

logger = logging.getLogger(__name__)


class CPU:
    """
    ARM7TDMI, a 32-bit RISC processor. It has a 3 stage instruction pipeline
    (fetch, decode, execute).

    The ARM7TDMI can operate in one of two different CPU states:
     - ARM, which uses a full instruction set with 32-bit opcodes
     - THUMB, which uses a cut-down instruction set with 16-bit opcodes

    https://problemkaputt.de/gbatek.htm#armcpureference
    """

    def __init__(self, scheduler: Scheduler, memory: Memory):
        self.scheduler = scheduler

        self.regs = Registers()
        self.regs.cpsr.mode = CPUMode.SYSTEM
        self.regs.spsr.mode = CPUMode.SYSTEM

        self.memory = memory
        self.memory.cpu = self

        self.pipeline = [0xF0000000, 0xF0000000]
        self.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    def step(self):
        irq_line = self.memory.io.interrupt_controller.irq_line

        if irq_line and not self.regs.cpsr.irq_disable:
            self.interrupt(ExceptionVector.EV_IRQ)

        power_down_mode = self.memory.io.interrupt_controller.power_down_mode

        if power_down_mode == PowerDownMode.NONE:
            if self.regs.cpsr.state == CPUState.ARM:
                self.step_arm()
            else:
                self.step_thumb()

        elif power_down_mode == PowerDownMode.HALT:
            self.scheduler.idle_until_next_event()

    def step_arm(self):
        instruction = self.pipeline[0]
        self.pipeline[0] = self.pipeline[1]
        self.pipeline[1] = self.memory.read_32(self.regs.pc, self.next_fetch_access)

        instruction_handler = arm_decode(instruction)

        cond = get_bits(instruction, 28, 31)
        if self.check_condition(cond):
            instruction_handler(self, instruction)
        else:
            # Skip instruction since condition was not met
            self.advance_pc_arm()
            self.next_fetch_access = MemoryAccess.SEQUENTIAL

    def step_thumb(self):
        instruction = self.pipeline[0]
        self.pipeline[0] = self.pipeline[1]
        self.pipeline[1] = self.memory.read_16(self.regs.pc, self.next_fetch_access)

        instruction_handler = thumb_decode(instruction)
        instruction_handler(self, instruction)

    def advance_pc_arm(self):
        self.regs.pc = add_32(self.regs.pc, ARM_PC_INCREMENT)

    def advance_pc_thumb(self):
        self.regs.pc = add_32(self.regs.pc, THUMB_PC_INCREMENT)

    def flush_pipeline(self):
        if self.regs.cpsr.state == CPUState.ARM:
            self.regs.pc &= ~0b11  # Align PC to 4 byte boundary
            self.pipeline[0] = self.memory.read_32(self.regs.pc, MemoryAccess.NON_SEQUENTIAL)
            self.advance_pc_arm()
            self.pipeline[1] = self.memory.read_32(self.regs.pc, MemoryAccess.SEQUENTIAL)
            self.advance_pc_arm()
        else:
            self.regs.pc &= ~0b1  # Align PC to 2 byte boundary
            self.pipeline[0] = self.memory.read_16(self.regs.pc, MemoryAccess.NON_SEQUENTIAL)
            self.advance_pc_thumb()
            self.pipeline[1] = self.memory.read_16(self.regs.pc, MemoryAccess.SEQUENTIAL)
            self.advance_pc_thumb()
        self.next_fetch_access = MemoryAccess.SEQUENTIAL

    def switch_mode(self, new_mode: CPUMode):
        self.regs.switch_mode(new_mode)

    def interrupt(self, vector: ExceptionVector):
        if vector == ExceptionVector.EV_RESET:
            new_mode = CPUMode.SWI
        elif vector == ExceptionVector.EV_UNDEFINED_INSTRUCTION:
            new_mode = CPUMode.UNDEFINED
        elif vector == ExceptionVector.EV_SWI:
            new_mode = CPUMode.SWI
        elif vector == ExceptionVector.EV_PREFETCH_ABORT:
            new_mode = CPUMode.ABORT
        elif vector == ExceptionVector.EV_DATA_ABORT:
            new_mode = CPUMode.ABORT
        elif vector == ExceptionVector.EV_ADDRESS_EXCEEDS_26_BITS:
            new_mode = CPUMode.SWI
        elif vector == ExceptionVector.EV_IRQ:
            new_mode = CPUMode.IRQ
        elif vector == ExceptionVector.EV_FIQ:
            new_mode = CPUMode.FIQ
        else:
            return

        cpsr_reg = self.regs.cpsr.reg
        self.switch_mode(new_mode)
        self.regs.spsr.reg = cpsr_reg

        if vector == ExceptionVector.EV_SWI or vector == ExceptionVector.EV_UNDEFINED_INSTRUCTION:
            self.regs.lr = add_32(self.regs.pc, -4 if self.regs.cpsr.state == CPUState.ARM else -2)
        elif vector != ExceptionVector.EV_RESET:
            self.regs.lr = add_32(self.regs.pc, -4 if self.regs.cpsr.state == CPUState.ARM else 0)

        self.regs.cpsr.state = CPUState.ARM
        self.regs.cpsr.irq_disable = True
        if vector in [ExceptionVector.EV_RESET, ExceptionVector.EV_FIQ]:
            self.regs.cpsr.fiq_disable = True

        self.regs.pc = vector
        self.flush_pipeline()

    def check_condition(self, cond: Condition | int) -> bint:
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
        else:
            return False

    def decode_and_compute_shift(self, value: int, shift: int) -> tuple[int, bint]:
        immediate = not get_bit(shift, 0)
        if immediate:
            shift_amount = get_bits(shift, 3, 7)
        else:
            shift_reg = get_bits(shift, 4, 7)
            shift_amount = self.regs[shift_reg] & 0xFF

        shift_type = get_bits(shift, 1, 2)

        return self.compute_shift(value, shift_type, shift_amount, immediate)

    def compute_shift(
        self, value: int, shift_type: ShiftType | int, shift_amount: int, immediate: bint
    ) -> tuple[int, bint]:
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
                mask = 0xFFFFFFFF
                result = (value << shift_amount) & mask
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
                mask = 0xFFFFFFFF
                result = (extend_sign_32(value) >> shift_amount) & mask

        elif shift_type == ShiftType.ROR:
            # ROR by n where n is greater than 32 will give the same result and carry out
            # as ROR by n-32; therefore, repeatedly subtract 32 from n until the amount is
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
