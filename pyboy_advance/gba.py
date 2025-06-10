import os
import time

from pyboy_advance.app.window import Window
from pyboy_advance.cpu.cpu import CPU
from pyboy_advance.cpu.registers import BankIndex
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.memory.io import IO
from pyboy_advance.memory.memory import Memory
from pyboy_advance.ppu.ppu import PPU
from pyboy_advance.scheduler import Scheduler


class PyBoyAdvance:
    def __init__(
        self,
        gamepak: GamePak | str | os.PathLike,
        bios: str | os.PathLike | None,
        skip_bios: bool = False,
    ):
        self.gamepak = (
            GamePak.from_file(gamepak) if isinstance(gamepak, (str, os.PathLike)) else gamepak
        )

        if bios:
            with open(bios, "rb") as bios_file:
                bios_data = bytearray(bios_file.read())
        else:
            bios_data = b""

        self.scheduler = Scheduler()
        self.ppu = PPU(self.scheduler)
        self.io = IO(self.ppu)
        self.memory = Memory(self.io, self.gamepak, bios_data)
        self.cpu = CPU(self.memory)

        if skip_bios:
            self.cpu.regs.banked_sp[BankIndex.SYSTEM_USER] = 0x03007F00
            self.cpu.regs.banked_sp[BankIndex.FIQ] = 0x03007F00
            self.cpu.regs.banked_sp[BankIndex.IRQ] = 0x03007FA0
            self.cpu.regs.banked_sp[BankIndex.SWI] = 0x03007FE0
            self.cpu.regs.banked_sp[BankIndex.ABORT] = 0x03007F00
            self.cpu.regs.banked_sp[BankIndex.UNDEFINED] = 0x03007F00
            self.cpu.regs.sp = 0x03007F00
            self.cpu.regs.pc = 0x08000000
            self.cpu.flush_pipeline()

    def step(self):
        self.cpu.step()
        self.scheduler.update(2)

    def run(self):
        window = Window()

        s = time.perf_counter()
        while True:
            self.step()
            if self.scheduler.cycles % 280896 == 0:
                e = time.perf_counter()
                print(e - s)
                s = time.perf_counter()

                window.get_events()
                window.render(self.ppu.frame_buffer_ptr)