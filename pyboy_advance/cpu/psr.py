import cython

from pyboy_advance.cpu.constants import CPUMode, CPUState
from pyboy_advance.utils import get_bit, set_bit


class ProgramStatusRegister:

    def __init__(self):
        self.reg = 0

    @property
    def mode(self) -> CPUMode:
        return CPUMode(self.reg & 0b11111)

    @mode.setter
    def mode(self, mode: CPUMode):
        self.reg = (self.reg & ~0b11111) | mode.value

    @property
    def state(self) -> CPUState:
        return CPUState(get_bit(self.reg, 5))

    @state.setter
    def state(self, state: CPUState):
        self.reg = set_bit(self.reg, 5, bool(state.value))

    @property
    def sign_flag(self) -> cython.bint:
        return get_bit(self.reg, 31)

    @sign_flag.setter
    def sign_flag(self, value: cython.bint):
        self.reg = set_bit(self.reg, 31, value)

    @property
    def zero_flag(self) -> cython.bint:
        return get_bit(self.reg, 30)

    @zero_flag.setter
    def zero_flag(self, value: cython.bint):
        self.reg = set_bit(self.reg, 30, value)

    @property
    def carry_flag(self) -> cython.bint:
        return get_bit(self.reg, 29)

    @carry_flag.setter
    def carry_flag(self, value: cython.bint):
        self.reg = set_bit(self.reg, 29, value)

    @property
    def overflow_flag(self) -> cython.bint:
        return get_bit(self.reg, 28)

    @overflow_flag.setter
    def overflow_flag(self, value: cython.bint):
        self.reg = set_bit(self.reg, 28, value)

    @property
    def sticky_overflow_flag(self) -> cython.bint:
        return get_bit(self.reg, 27)

    @sticky_overflow_flag.setter
    def sticky_overflow_flag(self, value: cython.bint):
        self.reg = set_bit(self.reg, 27, value)

    @property
    def irq_disable(self) -> cython.bint:
        return get_bit(self.reg, 7)

    @irq_disable.setter
    def irq_disable(self, value: cython.bint):
        self.reg = set_bit(self.reg, 7, value)

    @property
    def fiq_disable(self) -> cython.bint:
        return get_bit(self.reg, 6)

    @fiq_disable.setter
    def fiq_disable(self, value: cython.bint):
        self.reg = set_bit(self.reg, 6, value)
