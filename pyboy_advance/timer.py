# ifndef CYTHON
from __future__ import annotations

from pyboy_advance.constants import EventTrigger, Interrupt
from pyboy_advance.interrupt_controller import InterruptController
from pyboy_advance.scheduler import Scheduler, Event
from pyboy_advance.utils import bint, get_bit, get_bits, set_bit
# endif


class Timers:
    def __init__(
        self,
        scheduler: Scheduler,
        interrupt_controller: InterruptController,
    ):
        self.timer_3 = Timer(scheduler, interrupt_controller, Interrupt.TIMER_3, None)
        self.timer_2 = Timer(scheduler, interrupt_controller, Interrupt.TIMER_2, self.timer_3)
        self.timer_1 = Timer(scheduler, interrupt_controller, Interrupt.TIMER_1, self.timer_2)
        self.timer_0 = Timer(scheduler, interrupt_controller, Interrupt.TIMER_0, self.timer_1)


class Timer:
    def __init__(
        self,
        scheduler: Scheduler,
        interrupt_controller: InterruptController,
        interrupt: Interrupt,
        next_timer: Timer | None,
    ):
        self.WRITE_TIMER_REGISTER_DELAY = 1
        self.START_TIMER_DELAY = 1
        self.FREQUENCIES = [1, 64, 256, 1024]

        self.scheduler = scheduler
        self.interrupt_controller = interrupt_controller
        self.interrupt = interrupt
        self.next_timer = next_timer

        self._counter = 0
        self._reload_value = 0
        self._control_reg = 0

        self._pending_reload_value = 0
        self._pending_control_reg = 0

        self._overflow_event: Event | None = None

    @property
    def counter(self) -> int:
        if self.timer_enabled and not self.count_up:
            self._update_counter()
        return self._counter

    @counter.setter
    def counter(self, value: int):
        self._pending_reload_value = value
        self.scheduler.schedule(
            self._write_reload_value,
            self.WRITE_TIMER_REGISTER_DELAY,
            EventTrigger.IMMEDIATELY,
        )

    @property
    def control_reg(self) -> int:
        return self._control_reg

    @control_reg.setter
    def control_reg(self, value: int):
        self._pending_control_reg = value
        self.scheduler.schedule(
            self._write_control_reg,
            self.WRITE_TIMER_REGISTER_DELAY,
            EventTrigger.IMMEDIATELY,
        )

    @property
    def frequency(self) -> int:
        return self.FREQUENCIES[get_bits(self._control_reg, 0, 1)]

    @property
    def count_up(self) -> bint:
        return get_bit(self._control_reg, 2)

    @count_up.setter
    def count_up(self, value: bint):
        set_bit(self._control_reg, 2, value)

    @property
    def irq_enabled(self) -> bint:
        return get_bit(self._control_reg, 6)

    @property
    def timer_enabled(self) -> bint:
        return get_bit(self._control_reg, 7)

    def _write_reload_value(self):
        self._reload_value = self._pending_reload_value

    def _write_control_reg(self):
        old_count_up = self.count_up
        old_timer_enabled = self.timer_enabled

        self._control_reg = self._pending_control_reg

        new_count_up = self.count_up
        new_timer_enabled = self.timer_enabled

        if new_timer_enabled and not old_timer_enabled:
            self._start()
        elif not new_timer_enabled and old_timer_enabled:
            self._stop()
        elif new_count_up and not old_count_up:
            self._stop()
        elif not new_count_up and old_count_up:
            self._start()

    def _start(self):
        if not self.count_up:
            self._counter = self._reload_value
            self._schedule_overflow_event(self.START_TIMER_DELAY)
        elif self._overflow_event:
            self._schedule_overflow_event(0)

    def _stop(self):
        self._update_counter()

        if self._overflow_event:
            self._overflow_event.cancelled = True
            self._overflow_event = None

    def _update_counter(self):
        if self._overflow_event:
            elapsed = (self.scheduler.cycles - self._overflow_event.time) & 0xFFFF
            self._counter = elapsed // self.frequency

    def _schedule_overflow_event(self, start_delay: int):
        delay = (0x10000 - self._counter) * self.frequency + start_delay

        if self._overflow_event:
            self._overflow_event.cancelled = True
            self._overflow_event = None

        self._overflow_event = self.scheduler.schedule(
            self._overflow,
            delay,
            EventTrigger.IMMEDIATELY,
        )

    def _overflow(self):
        self._counter = self._reload_value

        if not self.count_up:
            self._schedule_overflow_event(0)
        elif self._overflow_event:
            self._overflow_event.cancelled = True
            self._overflow_event = None

        if self.irq_enabled:
            self.interrupt_controller.signal(self.interrupt)

        if self.next_timer and self.next_timer.count_up and self.next_timer.timer_enabled:
            self.next_timer._counter += 1
            if self.next_timer._counter == 0x10000:
                self.next_timer._overflow()
