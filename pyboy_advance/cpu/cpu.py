from pyboy_advance.cpu.constants import CPUMode, CPUState
from pyboy_advance.cpu.registers import Registers


class CPU:
    def __init__(self):
        self.regs = Registers()

    def step(self):
        if self.regs.cpsr.state == CPUState.ARM:
            pass
        else:
            pass

    def switch_mode(self, new_mode: CPUMode):
        self.regs.switch_mode(new_mode)
