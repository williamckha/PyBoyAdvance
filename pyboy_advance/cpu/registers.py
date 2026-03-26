# ifndef CYTHON
from __future__ import annotations

from array import array

from pyboy_advance.cpu.constants import CPUMode, CPUState, BankIndex
from pyboy_advance.utils import get_bit, set_bit, bint
# endif


class Registers:
    """
    ARM7TDMI register set. All registers are 32 bits wide.

    Only 16 registers are visible at any given time.
    There are 20 "banked" registers that get swapped in whenever the CPU
    switches to various privileged modes.
    """

    def __init__(self):
        self.SP = 13
        self.LR = 14
        self.PC = 15

        # General purpose registers R8 to R12 are banked
        self.BANKED_GPR_RANGE_START = 8
        self.BANKED_GPR_RANGE_END = 12
        self.BANKED_GPR_RANGE_LEN = self.BANKED_GPR_RANGE_END - self.BANKED_GPR_RANGE_START + 1

        self.regs = array("I", [0] * 16)
        self.cpsr = ProgramStatusRegister()  # Current program status register
        self.spsr = ProgramStatusRegister()  # Saved program status register

        # System/User mode and FIQ mode each have their own copy of R8 to R12
        self.banked_old_gpr = array("I", [0] * self.BANKED_GPR_RANGE_LEN)
        self.banked_fiq_gpr = array("I", [0] * self.BANKED_GPR_RANGE_LEN)

        # Every mode has its own SP and LR register
        self.banked_sp = array("I", [0] * len(BankIndex))
        self.banked_lr = array("I", [0] * len(BankIndex))

        # Every mode has its own SPSR register
        self.banked_spsr_user = ProgramStatusRegister()
        self.banked_spsr_fiq = ProgramStatusRegister()
        self.banked_spsr_irq = ProgramStatusRegister()
        self.banked_spsr_swi = ProgramStatusRegister()
        self.banked_spsr_abort = ProgramStatusRegister()
        self.banked_spsr_undefined = ProgramStatusRegister()

    def get(self, reg: int):
        return self.regs[reg]

    def set(self, reg: int, value: int):
        self.regs[reg] = value

    @property
    def sp(self):
        return self.regs[self.SP]

    @sp.setter
    def sp(self, value: int):
        self.regs[self.SP] = value

    @property
    def lr(self):
        return self.regs[self.LR]

    @lr.setter
    def lr(self, value: int):
        self.regs[self.LR] = value

    @property
    def pc(self):
        return self.regs[self.PC]

    @pc.setter
    def pc(self, value: int):
        self.regs[self.PC] = value

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

        old_bank_index = self.get_bank_index(old_mode)
        new_bank_index = self.get_bank_index(new_mode)

        self.banked_sp[old_bank_index] = self.sp
        self.banked_lr[old_bank_index] = self.lr
        self.get_banked_spsr(old_bank_index).reg = self.spsr.reg

        self.sp = self.banked_sp[new_bank_index]
        self.lr = self.banked_lr[new_bank_index]
        self.spsr.reg = self.get_banked_spsr(new_bank_index).reg

        if new_mode == CPUMode.FIQ:
            for i in range(self.BANKED_GPR_RANGE_LEN):
                self.banked_old_gpr[i] = self.regs[i + self.BANKED_GPR_RANGE_START]
                self.regs[i + self.BANKED_GPR_RANGE_START] = self.banked_fiq_gpr[i]
        elif old_mode == CPUMode.FIQ:
            for i in range(self.BANKED_GPR_RANGE_LEN):
                self.banked_fiq_gpr[i] = self.regs[i + self.BANKED_GPR_RANGE_START]
                self.regs[i + self.BANKED_GPR_RANGE_START] = self.banked_old_gpr[i]

    def get_bank_index(self, mode: CPUMode) -> BankIndex:
        if mode == CPUMode.SYSTEM or mode == CPUMode.USER:
            return BankIndex.BANK_SYSTEM_USER
        elif mode == CPUMode.FIQ:
            return BankIndex.BANK_FIQ
        elif mode == CPUMode.IRQ:
            return BankIndex.BANK_IRQ
        elif mode == CPUMode.SWI:
            return BankIndex.BANK_SWI
        elif mode == CPUMode.ABORT:
            return BankIndex.BANK_ABORT
        elif mode == CPUMode.UNDEFINED:
            return BankIndex.BANK_UNDEFINED
        # ifndef CYTHON
        raise ValueError("Invalid CPU mode")
        # endif

    def get_banked_spsr(self, bank_index: BankIndex) -> ProgramStatusRegister:
        if bank_index == BankIndex.BANK_SYSTEM_USER:
            return self.banked_spsr_user
        if bank_index == BankIndex.BANK_FIQ:
            return self.banked_spsr_fiq
        elif bank_index == BankIndex.BANK_IRQ:
            return self.banked_spsr_irq
        elif bank_index == BankIndex.BANK_SWI:
            return self.banked_spsr_swi
        elif bank_index == BankIndex.BANK_ABORT:
            return self.banked_spsr_abort
        elif bank_index == BankIndex.BANK_UNDEFINED:
            return self.banked_spsr_undefined
        # ifndef CYTHON
        raise ValueError("Invalid bank index")
        # endif


class ProgramStatusRegister:
    def __init__(self, value: int = 0):
        self.reg = value

    @property
    def mode(self) -> CPUMode | int:
        return self.reg & 0b11111

    @mode.setter
    def mode(self, mode: CPUMode):
        self.reg = (self.reg & ~0b11111) | mode

    @property
    def state(self) -> CPUState | int:
        return get_bit(self.reg, 5)

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
