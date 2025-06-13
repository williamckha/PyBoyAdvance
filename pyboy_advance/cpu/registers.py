from enum import IntEnum

from pyboy_advance.cpu.constants import CPUMode, CPUState
from pyboy_advance.utils import get_bit, set_bit, bint


class Registers:
    """
    ARM7TDMI register set. All registers are 32 bits wide.

    Only 16 registers are visible at any given time.
    There are 20 "banked" registers that get swapped in whenever the CPU
    switches to various privileged modes.
    """

    SP = 13
    LR = 14
    PC = 15

    # General purpose registers R8 to R12 are banked
    BANKED_GPR_RANGE_START = 8
    BANKED_GPR_RANGE_END = 12
    BANKED_GPR_RANGE_LEN = BANKED_GPR_RANGE_END - BANKED_GPR_RANGE_START + 1

    def __init__(self):
        self.regs = [0] * 16
        self.cpsr = ProgramStatusRegister()  # Current program status register
        self.spsr = ProgramStatusRegister()  # Saved program status register

        # System/User mode and FIQ mode each have their own copy of R8 to R12
        self.banked_old_gpr = [0] * Registers.BANKED_GPR_RANGE_LEN
        self.banked_fiq_gpr = [0] * Registers.BANKED_GPR_RANGE_LEN

        # Every mode has its own SP and LR register
        self.banked_sp = [0] * len(BankIndex)
        self.banked_lr = [0] * len(BankIndex)

        # Every mode except System/User mode has its own SPSR register
        # (self.banked_spsr[BankIndex.SYSTEM_USER] is unused)
        self.banked_spsr = [ProgramStatusRegister() for _ in range(len(BankIndex))]

    def __getitem__(self, reg: int):
        return self.regs[reg]

    def __setitem__(self, reg: int, value: int):
        self.regs[reg] = value

    @property
    def sp(self):
        return self.regs[Registers.SP]

    @sp.setter
    def sp(self, value: int):
        self.regs[Registers.SP] = value

    @property
    def lr(self):
        return self.regs[Registers.LR]

    @lr.setter
    def lr(self, value: int):
        self.regs[Registers.LR] = value

    @property
    def pc(self):
        return self.regs[Registers.PC]

    @pc.setter
    def pc(self, value: int):
        self.regs[Registers.PC] = value

    def switch_mode(self, new_mode: CPUMode):
        """
        Switch from the current mode to the specified mode.

        Saves the current register values to the current mode's bank and
        replaces them with values from the new mode's bank.
        """
        if new_mode == self.cpsr.mode:
            return

        old_mode = self.cpsr.mode
        self.cpsr.mode = new_mode

        old_bank_index = BankIndex.from_cpu_mode(old_mode)
        new_bank_index = BankIndex.from_cpu_mode(new_mode)

        self.banked_sp[old_bank_index] = self.sp
        self.banked_lr[old_bank_index] = self.lr
        self.banked_spsr[old_bank_index].reg = self.spsr.reg

        self.sp = self.banked_sp[new_bank_index]
        self.lr = self.banked_lr[new_bank_index]
        self.spsr.reg = self.banked_spsr[new_bank_index].reg

        if new_mode == CPUMode.FIQ:
            for i in range(Registers.BANKED_GPR_RANGE_LEN):
                self.banked_old_gpr[i] = self.regs[i + Registers.BANKED_GPR_RANGE_START]
                self.regs[i + Registers.BANKED_GPR_RANGE_START] = self.banked_fiq_gpr[i]
        elif old_mode == CPUMode.FIQ:
            for i in range(Registers.BANKED_GPR_RANGE_LEN):
                self.banked_fiq_gpr[i] = self.regs[i + Registers.BANKED_GPR_RANGE_START]
                self.regs[i + Registers.BANKED_GPR_RANGE_START] = self.banked_old_gpr[i]


class ProgramStatusRegister:
    def __init__(self, value: int = 0):
        self.reg = value

    @property
    def mode(self) -> CPUMode:
        return CPUMode(self.reg & 0b11111)

    @mode.setter
    def mode(self, mode: CPUMode):
        self.reg = (self.reg & ~0b11111) | mode

    @property
    def state(self) -> CPUState:
        return CPUState(get_bit(self.reg, 5))

    @state.setter
    def state(self, state: CPUState):
        self.reg = set_bit(self.reg, 5, state)

    @property
    def sign_flag(self) -> bint:
        return get_bit(self.reg, 31)

    @sign_flag.setter
    def sign_flag(self, value: bint):
        self.reg = set_bit(self.reg, 31, value)

    @property
    def zero_flag(self) -> bint:
        return get_bit(self.reg, 30)

    @zero_flag.setter
    def zero_flag(self, value: bint):
        self.reg = set_bit(self.reg, 30, value)

    @property
    def carry_flag(self) -> bint:
        return get_bit(self.reg, 29)

    @carry_flag.setter
    def carry_flag(self, value: bint):
        self.reg = set_bit(self.reg, 29, value)

    @property
    def overflow_flag(self) -> bint:
        return get_bit(self.reg, 28)

    @overflow_flag.setter
    def overflow_flag(self, value: bint):
        self.reg = set_bit(self.reg, 28, value)

    @property
    def sticky_overflow_flag(self) -> bint:
        return get_bit(self.reg, 27)

    @sticky_overflow_flag.setter
    def sticky_overflow_flag(self, value: bint):
        self.reg = set_bit(self.reg, 27, value)

    @property
    def irq_disable(self) -> bint:
        return get_bit(self.reg, 7)

    @irq_disable.setter
    def irq_disable(self, value: bint):
        self.reg = set_bit(self.reg, 7, value)

    @property
    def fiq_disable(self) -> bint:
        return get_bit(self.reg, 6)

    @fiq_disable.setter
    def fiq_disable(self, value: bint):
        self.reg = set_bit(self.reg, 6, value)


class BankIndex(IntEnum):
    SYSTEM_USER = 0
    FIQ = 1
    IRQ = 2
    SWI = 3
    ABORT = 4
    UNDEFINED = 5

    @staticmethod
    def from_cpu_mode(mode: CPUMode):
        if mode == CPUMode.SYSTEM or mode == CPUMode.USER:
            return BankIndex.SYSTEM_USER
        elif mode == CPUMode.FIQ:
            return BankIndex.FIQ
        elif mode == CPUMode.IRQ:
            return BankIndex.IRQ
        elif mode == CPUMode.SWI:
            return BankIndex.SWI
        elif mode == CPUMode.ABORT:
            return BankIndex.ABORT
        elif mode == CPUMode.UNDEFINED:
            return BankIndex.UNDEFINED
