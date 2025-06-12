from __future__ import annotations

import functools
from enum import IntFlag

from pyboy_advance.scheduler import Scheduler


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

    @property
    def interrupt_enable(self):
        return self._interrupt_enable

    @interrupt_enable.setter
    def interrupt_enable(self, value):
        self._interrupt_enable = value
        self._schedule_write_interrupt_registers()

    @property
    def interrupt_flags(self):
        return self._interrupt_flags

    @interrupt_flags.setter
    def interrupt_flags(self, value):
        self._interrupt_flags = value
        self._schedule_write_interrupt_registers()

    @property
    def interrupt_master_enable(self):
        return self._interrupt_master_enable

    @interrupt_master_enable.setter
    def interrupt_master_enable(self, value):
        self._interrupt_master_enable = value
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
        new_irq_line = interrupt_available and self._interrupt_master_enable

        if new_irq_line != self.irq_line:
            self.scheduler.schedule(
                functools.partial(self._update_irq_line, new_irq_line),
                InterruptController.UPDATE_IRQ_LINE_DELAY,
            )

    def _update_irq_line(self, new_irq_line):
        self.irq_line = new_irq_line


class Interrupt(IntFlag):
    VBLANK = 1
    HBLANK = 2
    VCOUNT = 4
    TIMER_0 = 8
    TIMER_1 = 16
    TIMER_2 = 32
    TIMER_3 = 64
    SERIAL = 128
    DMA_0 = 256
    DMA_1 = 512
    DMA_2 = 1024
    DMA_3 = 2048
    KEYPAD = 4096
    GAMEPAK = 8192

