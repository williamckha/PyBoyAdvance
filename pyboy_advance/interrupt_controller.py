from __future__ import annotations

import functools
from enum import IntFlag, auto, IntEnum

from pyboy_advance.scheduler import Scheduler
from pyboy_advance.utils import bint


class Interrupt(IntFlag):
    # fmt: off
    VBLANK      = auto()
    HBLANK      = auto()
    VCOUNT      = auto()
    TIMER_0     = auto()
    TIMER_1     = auto()
    TIMER_2     = auto()
    TIMER_3     = auto()
    SERIAL      = auto()
    DMA_0       = auto()
    DMA_1       = auto()
    DMA_2       = auto()
    DMA_3       = auto()
    KEYPAD      = auto()
    GAMEPAK     = auto()
    ALL         = 0x3FFF
    # fmt: on


class PowerDownMode(IntEnum):
    NONE = 0
    HALT = 1
    STOP = 2


class InterruptController:
    WRITE_INTERRUPT_REGISTERS_DELAY = 1
    UPDATE_IRQ_LINE_DELAY = 2

    def __init__(self, scheduler: Scheduler):
        self.scheduler = scheduler

        self._interrupt_enable = 0
        self._interrupt_flags = 0
        self._interrupt_master_enable = 0

        self._pending_interrupt_enable = 0
        self._pending_interrupt_flags = 0
        self._pending_interrupt_master_enable = 0

        self.irq_line = False

        self.power_down_mode = PowerDownMode.NONE

    @property
    def interrupt_enable(self) -> int:
        return self._interrupt_enable

    @interrupt_enable.setter
    def interrupt_enable(self, value: int):
        self._pending_interrupt_enable = value & Interrupt.ALL
        self._schedule_write_interrupt_registers()

    @property
    def interrupt_flags(self) -> int:
        return self._interrupt_flags

    @interrupt_flags.setter
    def interrupt_flags(self, value: int):
        self._pending_interrupt_flags &= ~value
        self._schedule_write_interrupt_registers()

    @property
    def interrupt_master_enable(self) -> bint:
        return self._interrupt_master_enable

    @interrupt_master_enable.setter
    def interrupt_master_enable(self, value: bint):
        self._pending_interrupt_master_enable = value & 0b1
        self._schedule_write_interrupt_registers()

    def signal(self, interrupt: Interrupt):
        self._pending_interrupt_flags |= interrupt
        self._schedule_write_interrupt_registers()

    def _schedule_write_interrupt_registers(self):
        self.scheduler.schedule(
            self._write_interrupt_registers,
            InterruptController.WRITE_INTERRUPT_REGISTERS_DELAY,
        )

    def _write_interrupt_registers(self):
        self._interrupt_enable = self._pending_interrupt_enable
        self._interrupt_flags = self._pending_interrupt_flags
        self._interrupt_master_enable = self._pending_interrupt_master_enable

        interrupt_available = self._interrupt_enable & self._interrupt_flags

        if interrupt_available and self.power_down_mode == PowerDownMode.HALT:
            self.power_down_mode = PowerDownMode.NONE

        new_irq_line = interrupt_available and self._interrupt_master_enable
        if new_irq_line != self.irq_line:
            self.scheduler.schedule(
                functools.partial(self._update_irq_line, new_irq_line),
                InterruptController.UPDATE_IRQ_LINE_DELAY,
            )

    def _update_irq_line(self, new_irq_line: bool):
        self.irq_line = new_irq_line
