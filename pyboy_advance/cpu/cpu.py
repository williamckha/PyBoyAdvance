from pyboy_advance.cpu.constants import CPUMode, CPUState
from pyboy_advance.cpu.psr import ProgramStatusRegister


class CPU:

    def __init__(self):
        # General purpose registers
        self.gpr = [0] * 13
        # Stack pointer register (R13)
        self.sp = 0
        # Link register (R14)
        self.lr = 0
        # Program counter register (R15)
        self.pc = 0
        # Current program status register
        self.cpsr = ProgramStatusRegister()
        # Saved program status register
        self.spsr = ProgramStatusRegister()

        # Some registers are "banked" (register has multiple copies, one copy per mode)
        # User mode and FIQ mode each have their own copy of registers 8 to 12
        self.banked_gpr_r8_r12 = [0] * 5

        # Every mode its own SP and LR register
        self.banked_sp = [0] * len(CPUMode)
        self.banked_lr = [0] * len(CPUMode)

        # Every mode except user mode has its own SPSR register
        # (self.banked_spsr[0] is unused)
        self.banked_spsr = [ProgramStatusRegister() for _ in range(len(CPUMode))]

    def step(self):
        if self.cpsr.state == CPUState.ARM:
            pass
        else:
            pass

    def get_reg(self, reg):
        if reg < len(self.gpr):
            return self.gpr[reg]
        elif reg == 13:
            return self.sp
        elif reg == 14:
            return self.lr
        elif reg == 15:
            return self.pc

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

        def get_bank_index(mode: CPUMode):
            if mode == CPUMode.USER or mode == CPUMode.SYSTEM:
                return 0
            elif mode == CPUMode.FIQ:
                return 1
            elif mode == CPUMode.IRQ:
                return 2
            elif mode == CPUMode.SWI:
                return 3
            elif mode == CPUMode.ABORT:
                return 4
            elif mode == CPUMode.UNDEFINED:
                return 5

        old_bank_index = get_bank_index(old_mode)
        new_bank_index = get_bank_index(new_mode)

        self.banked_sp[old_bank_index] = self.sp
        self.banked_lr[old_bank_index] = self.lr
        self.banked_spsr[old_bank_index] = self.spsr

        self.sp = self.banked_sp[new_bank_index]
        self.lr = self.banked_lr[new_bank_index]
        self.spsr = self.banked_spsr[new_bank_index]

        if old_mode == CPUMode.FIQ or new_mode == CPUMode.FIQ:
            for i in range(len(self.banked_gpr_r8_r12)):
                self.gpr[i + 8], self.banked_gpr_r8_r12[i] = (
                    self.banked_gpr_r8_r12[i], self.gpr[i + 8]
                )
