# ifndef CYTHON
from time import perf_counter_ns

from pyboy_advance.api.screen import Screen
from pyboy_advance.app.constants import WindowEvent
from pyboy_advance.app.window import Window
from pyboy_advance.constants import CLOCK_SPEED_HZ, NANOSECONDS_PER_SECOND, EventTrigger, Key
from pyboy_advance.cpu.constants import ExceptionVector, BankIndex
from pyboy_advance.cpu.cpu import CPU
from pyboy_advance.cpu.arm.decode import arm_decoder
from pyboy_advance.cpu.thumb.decode import thumb_decoder
from pyboy_advance.interrupt_controller import InterruptController
from pyboy_advance.keypad import Keypad
from pyboy_advance.memory.dma import DMAController
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.memory.io import IO
from pyboy_advance.memory.memory import Memory
from pyboy_advance.ppu.constants import CYCLES_FRAME
from pyboy_advance.ppu.ppu import PPU
from pyboy_advance.scheduler import Scheduler
from pyboy_advance.timer import Timers
# endif

import os

from time import sleep


class PyBoyAdvance:
    def __init__(
        self,
        rom: GamePak | str | os.PathLike,
        bios: str | os.PathLike | None = None,
        skip_bios: bool = False,
        emulation_speed: float = 0,
    ):
        self.gamepak = GamePak.from_file(rom) if isinstance(rom, (str, os.PathLike)) else rom

        if bios:
            with open(bios, "rb") as bios_file:
                bios_data = bytearray(bios_file.read())
        else:
            bios_data = b""

        self.scheduler = Scheduler()
        self.memory = Memory(self.scheduler, self.gamepak, bios_data)

        self.interrupt_controller = InterruptController(self.scheduler)
        self.dma_controller = DMAController(self.scheduler, self.memory)
        self.timers = Timers(self.scheduler, self.interrupt_controller)
        self.ppu = PPU(self.scheduler, self.interrupt_controller)
        self.keypad = Keypad(self.interrupt_controller)
        self.memory.io = IO(
            self.memory,
            self.interrupt_controller,
            self.dma_controller,
            self.timers,
            self.ppu,
            self.keypad,
        )

        self.cpu = CPU(self.scheduler, self.memory)
        self.cpu.arm_decoder = arm_decoder
        self.cpu.thumb_decoder = thumb_decoder

        self._time_per_frame = 0
        self._last_frame_time = 0
        self._accumulated_time = 0

        self.set_emulation_speed(emulation_speed)
        self.scheduler.schedule(self._frame_limiter, CYCLES_FRAME, EventTrigger.IMMEDIATELY)

        self._frame_overshoot = 0

        if skip_bios:
            self.memory.bios_last_opcode = 0xE129F000
            self.cpu.regs.banked_sp[int(BankIndex.BANK_SYSTEM_USER)] = 0x03007F00
            self.cpu.regs.banked_sp[int(BankIndex.BANK_FIQ)] = 0x03007F00
            self.cpu.regs.banked_sp[int(BankIndex.BANK_IRQ)] = 0x03007FA0
            self.cpu.regs.banked_sp[int(BankIndex.BANK_SWI)] = 0x03007FE0
            self.cpu.regs.banked_sp[int(BankIndex.BANK_ABORT)] = 0x03007F00
            self.cpu.regs.banked_sp[int(BankIndex.BANK_UNDEFINED)] = 0x03007F00
            self.cpu.regs.sp = 0x03007F00
            self.cpu.regs.pc = 0x08000000
            self.cpu.flush_pipeline()
        else:
            self.cpu.interrupt(ExceptionVector.RESET)

        self.screen = Screen(self.ppu)

    def step(self):
        if self.dma_controller.active:
            self.dma_controller.perform_transfers()
        else:
            self.cpu.step()

    def frame(self, count: int = 1, render: bool = True):
        self.ppu.rendering_enabled = False

        for frame_num in range(count):
            if frame_num == count - 1 and render:
                self.ppu.rendering_enabled = True

            end_time = self.scheduler.cycles + CYCLES_FRAME - self._frame_overshoot
            while self.scheduler.cycles < end_time:
                self.step()
            self._frame_overshoot = self.scheduler.cycles - end_time

    def run(self):
        with Window() as window:
            running = True
            while running:
                self.frame()

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

    def press_key(self, key: Key):
        self.keypad.press_key(key)

    def release_key(self, key: Key):
        self.keypad.release_key(key)

    def set_emulation_speed(self, speed: float):
        if speed < 0:
            raise ValueError("Emulation speed must be 0 or greater")

        self._time_per_frame = (
            int((1 / (speed * CLOCK_SPEED_HZ / CYCLES_FRAME)) * NANOSECONDS_PER_SECOND)
            if speed > 0
            else 0
        )

        self._last_frame_time = perf_counter_ns()
        self._accumulated_time = 0

    def _frame_limiter(self):
        self.scheduler.schedule(self._frame_limiter, CYCLES_FRAME, EventTrigger.IMMEDIATELY)

        if self._time_per_frame == 0:
            return

        now = perf_counter_ns()
        self._accumulated_time += now - self._last_frame_time
        self._last_frame_time = now

        if self._accumulated_time < self._time_per_frame:
            delay = (self._time_per_frame - self._accumulated_time) / float(NANOSECONDS_PER_SECOND)
            sleep(delay)

        self._accumulated_time -= self._time_per_frame
