import os

from pyboy_advance.cpu.cpu import CPU
from pyboy_advance.cpu.registers import BankIndex
from pyboy_advance.interrupt_controller import InterruptController
from pyboy_advance.keypad import Keypad, Key
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.memory.io import IO
from pyboy_advance.memory.memory import Memory
from pyboy_advance.ppu.ppu import PPU
from pyboy_advance.scheduler import Scheduler
from pyboy_advance.app.window import Window, WindowEvent


class PyBoyAdvance:
    def __init__(
        self,
        gamepak: GamePak | str | os.PathLike,
        bios: str | os.PathLike | None = None,
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
        self.interrupt_controller = InterruptController(self.scheduler)
        self.ppu = PPU(self.scheduler, self.interrupt_controller)
        self.keypad = Keypad()
        self.io = IO(self.interrupt_controller, self.ppu, self.keypad)
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
        with Window() as window:
            running = True
            while running:
                self.step()
                if self.scheduler.cycles % 280896 == 0:
                    for event in window.get_events():
                        if event == WindowEvent.NONE:
                            continue
                        elif event == WindowEvent.QUIT:
                            running = False
                        elif event == WindowEvent.FULLSCREEN:
                            window.fullscreen = not window.fullscreen
                        else:
                            self.keypad.process_window_event(event)
                    window.render(self.ppu.frame_buffer_ptr)
