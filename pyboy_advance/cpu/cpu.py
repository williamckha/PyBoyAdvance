from pyboy_advance.cpu.arm.decode import arm_decode
from pyboy_advance.cpu.constants import CPUMode, CPUState, ARMCondition, ARM_PC_INCREMENT, THUMB_PC_INCREMENT
from pyboy_advance.cpu.registers import Registers
from pyboy_advance.memory.memory import MemoryAccess, Memory
from pyboy_advance.utils import get_bits


class CPU:
    def __init__(self):
        self.regs = Registers()
        self.regs.cpsr.mode = CPUMode.SYSTEM

        self.memory = Memory(self)

        self.pipeline = [0xF0000000, 0xF0000000]
        self.next_fetch_access = MemoryAccess.NON_SEQUENTIAL

    def step(self):
        if self.regs.cpsr.state == CPUState.ARM:
            instruction = self.pipeline[0]
            self.pipeline[0] = self.pipeline[1]
            self.pipeline[1] = self.memory.read_32(self.regs.pc, self.next_fetch_access)

            cond = ARMCondition(get_bits(instruction, 28, 31))
            if self.check_condition(cond):
                instruction_func = arm_decode(instruction)
                instruction_func(self, instruction)
            else:
                # Skip instruction since condition was not met
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
        self.regs.pc = (self.regs.pc + ARM_PC_INCREMENT) & 0xFFFFFFFF

    def thumb_advance_pc(self):
        self.regs.pc = (self.regs.pc + THUMB_PC_INCREMENT) & 0xFFFFFFFF

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

    def skip_bios(self):
        self.regs.skip_bios()
        self.flush_pipeline()
