# ifndef CYTHON
from __future__ import annotations

from pyboy_advance.constants import Interrupt, PowerDownMode, EventTrigger
from pyboy_advance.scheduler import Scheduler
from pyboy_advance.utils import bint
# endif


class InterruptController:
    def __init__(self, scheduler: Scheduler):
        self.WRITE_INTERRUPT_REGISTERS_DELAY = 1
        self.UPDATE_IRQ_LINE_DELAY = 2

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
            self.WRITE_INTERRUPT_REGISTERS_DELAY,
            EventTrigger.TRIG_IMMEDIATELY,
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
            if new_irq_line:
                self.scheduler.schedule(
                    self._set_irq_line,
                    self.UPDATE_IRQ_LINE_DELAY,
                    EventTrigger.TRIG_IMMEDIATELY,
                )
            else:
                self.scheduler.schedule(
                    self._reset_irq_line,
                    self.UPDATE_IRQ_LINE_DELAY,
                    EventTrigger.TRIG_IMMEDIATELY,
                )

    def _set_irq_line(self):
        self.irq_line = True

    def _reset_irq_line(self):
        self.irq_line = False
