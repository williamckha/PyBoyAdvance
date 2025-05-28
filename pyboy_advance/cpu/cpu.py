from pyboy_advance.cpu.arm.decode import arm_decode
from pyboy_advance.cpu.constants import CPUMode, CPUState, ARMCondition, ARM_PC_INCREMENT, THUMB_PC_INCREMENT, \
    ARMShiftType
from pyboy_advance.cpu.registers import Registers
from pyboy_advance.memory.memory import MemoryAccess, Memory
from pyboy_advance.utils import get_bits, get_bit, ror_32, add_uint_to_uint


class CPU:
    def __init__(self, memory: Memory):
        self.regs = Registers()
        self.regs.cpsr.mode = CPUMode.SYSTEM

        self.memory = memory
        self.memory.connect_cpu(self)

        self.pipeline = [0xF0000000, 0xF0000000]
        self.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    def step(self):
        if self.regs.cpsr.state == CPUState.ARM:
            instruction = self.pipeline[0]
            self.pipeline[0] = self.pipeline[1]
            self.pipeline[1] = self.memory.read_32(self.regs.pc, self.next_fetch_access)

            instruction_func = arm_decode(instruction)

            cond = ARMCondition(get_bits(instruction, 28, 31))
            if self.check_condition(cond):
                print("Executing <{0:#010x}> {1:032b} {2}".format(
                    (self.regs.pc - 8),
                    instruction,
                    instruction_func.__name__,
                ))
                instruction_func(self, instruction)
            else:
                # Skip instruction since condition was not met
                print("Skipping  <{0:#010x}> {1:032b} {2}".format(
                    (self.regs.pc - 8),
                    instruction,
                    instruction_func.__name__,
                ))
                self.arm_advance_pc()
                self.next_fetch_access = MemoryAccess.SEQUENTIAL
        else:
            raise NotImplementedError("Thumb mode not implemented")

    def flush_pipeline(self):
        if self.regs.cpsr.state == CPUState.ARM:
            self.pipeline[0] = self.memory.read_32(self.regs.pc, MemoryAccess.NON_SEQUENTIAL)
            self.arm_advance_pc()
            self.pipeline[1] = self.memory.read_32(self.regs.pc, MemoryAccess.SEQUENTIAL)
            self.arm_advance_pc()
        else:
            self.pipeline[0] = self.memory.read_16(self.regs.pc, MemoryAccess.NON_SEQUENTIAL)
            self.thumb_advance_pc()
            self.pipeline[1] = self.memory.read_16(self.regs.pc, MemoryAccess.SEQUENTIAL)
            self.thumb_advance_pc()
        self.next_fetch_access = MemoryAccess.SEQUENTIAL

    def arm_advance_pc(self):
        self.regs.pc = add_uint_to_uint(self.regs.pc, ARM_PC_INCREMENT)

    def thumb_advance_pc(self):
        self.regs.pc = add_uint_to_uint(self.regs.pc, THUMB_PC_INCREMENT)

    def switch_mode(self, new_mode: CPUMode):
        self.regs.switch_mode(new_mode)

    def check_condition(self, cond: ARMCondition) -> bool:
        cpsr = self.regs.cpsr
        match cond:
            case ARMCondition.EQ:
                return cpsr.zero_flag
            case ARMCondition.NE:
                return not cpsr.zero_flag
            case ARMCondition.HS:
                return cpsr.carry_flag
            case ARMCondition.LO:
                return not cpsr.carry_flag
            case ARMCondition.MI:
                return cpsr.sign_flag
            case ARMCondition.PL:
                return not cpsr.sign_flag
            case ARMCondition.VS:
                return cpsr.overflow_flag
            case ARMCondition.VC:
                return not cpsr.overflow_flag
            case ARMCondition.HI:
                return cpsr.carry_flag and not cpsr.zero_flag
            case ARMCondition.LS:
                return not cpsr.carry_flag or cpsr.zero_flag
            case ARMCondition.GE:
                return cpsr.sign_flag == cpsr.overflow_flag
            case ARMCondition.LT:
                return cpsr.sign_flag != cpsr.overflow_flag
            case ARMCondition.GT:
                return not cpsr.zero_flag and cpsr.sign_flag == cpsr.overflow_flag
            case ARMCondition.LE:
                return cpsr.zero_flag or cpsr.sign_flag != cpsr.overflow_flag
            case ARMCondition.AL:
                return True
            case ARMCondition.NV:
                raise ValueError("Condition NV (never) is reserved")
            case _:
                raise ValueError

    def compute_shift(self, value: int, shift: int) -> tuple[int, bool]:
        carry_out = 0

        immediate = get_bit(shift, 0)
        if immediate:
            shift_amount = get_bits(shift, 3, 7)
        else:
            shift_reg = get_bits(shift, 4, 7)
            shift_amount = self.regs[shift_reg] & 0xFF
            if shift_amount == 0:
                return value, self.regs.cpsr.carry_flag

        match ARMShiftType(get_bits(shift, 1, 2)):

            case ARMShiftType.LSL:
                # LSL#0 and Immediate: No shift performed, i.e. directly Op2=Rm, the C flag is NOT affected.
                # LSL#32 has result zero, carry out equal to bit 0 of Rm.
                # LSL by more than 32 has result zero, carry out zero.
                if shift_amount == 0:
                    carry_out = self.regs.cpsr.carry_flag
                elif shift_amount < 32:
                    carry_out = get_bit(value >> (32 - shift_amount), 0)
                    value = (value << shift_amount) & 0xFFFFFFFF
                elif shift_amount == 32:
                    carry_out = get_bit(value, 0)
                    value = 0
                else:
                    carry_out = False
                    value = 0

            case ARMShiftType.LSR:
                # LSR#0 and Immediate: Interpreted as LSR#32, i.e. Op2 becomes zero, C becomes Bit 31 of Rm.
                # LSR#32 has result zero, carry out equal to bit 31 of Rm.
                # LSR by more than 32 has result zero, carry out zero.
                if shift_amount == 0:
                    carry_out = get_bit(value, 31)
                    value = 0
                elif shift_amount < 32:
                    carry_out = get_bit(value >> (shift_amount - 1), 0)
                    value = value >> shift_amount
                elif shift_amount == 32:
                    carry_out = get_bit(value, 31)
                    value = 0
                else:
                    carry_out = False
                    value = 0

            case ARMShiftType.ASR:
                # ASR#0 and Immediate = 0: Interpreted as ASR#32, i.e. Op2 and C are filled by Bit 31 of Rm.
                # ASR by 32 or more has result filled with and carry out equal to bit 31 of Rm.
                if shift_amount == 0 or shift_amount >= 32:
                    carry_out = get_bit(value, 31)
                    value = 0xFFFFFFFF if carry_out else 0
                else:
                    carry_out = get_bit(value >> (shift_amount - 1), 0)
                    value = value >> shift_amount

            case ARMShiftType.ROR:
                # ROR#0 and Immediate = 0: Interpreted as RRX#1 (RCR), like ROR#1, but Op2 Bit 31 set to old C.
                # ROR#32 has result equal to Rm, carry out equal to bit 31 of Rm.
                # ROR by n where n is greater than 32 will give the same result and carry out
                # as ROR by n-32; therefore repeatedly subtract 32 from n until the amount is
                # in the range 1 to 32 and see above.
                if shift_amount > 32:
                    shift_amount = ((shift_amount - 1) % 32) + 1

                if shift_amount == 0:
                    carry_out = get_bit(value, 0)
                    value = (value >> 1) | (self.regs.cpsr.carry_flag << 31)
                else:
                    carry_out = get_bit(value >> (shift_amount - 1), 0)
                    value = ror_32(value, get_bits(shift_amount, 0, 4))

        return value, carry_out
