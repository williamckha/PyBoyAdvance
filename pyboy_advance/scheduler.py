# ifndef CYTHON
from typing import Callable

from pyboy_advance.constants import EventTrigger
# endif

import heapq


class Event:
    def __init__(
        self,
        callback: Callable[[], None],
        delay: int,
        time: int,
        cancelled: bool,
    ):
        self.callback = callback
        self.delay = delay
        self.time = time
        self.cancelled = cancelled

    def __lt__(self, other):
        return self.time < other.time


class Scheduler:
    def __init__(self):
        self.cycles = 0
        self.events = []
        self.inactive_events = {}

    def schedule(
        self,
        callback: Callable[[], None],
        delay: int,
        trigger: EventTrigger,
    ) -> Event:
        event = Event(callback, delay, 0, False)
        if trigger == EventTrigger.IMMEDIATELY:
            event.time = self.cycles + delay
            heapq.heappush(self.events, event)
        else:
            if trigger not in self.inactive_events:
                self.inactive_events[trigger] = []
            self.inactive_events[trigger].append(event)
        return event

    def trigger(self, trigger: EventTrigger):
        if trigger not in self.inactive_events:
            self.inactive_events[trigger] = []

        while self.inactive_events[trigger]:
            event = self.inactive_events[trigger].pop()
            event.time = self.cycles + event.delay
            heapq.heappush(self.events, event)

    def idle(self, cycles: int):
        self.cycles += cycles

    def idle_until_next_event(self):
        if self.events:
            event = self.events[0]
            if event.time > self.cycles:
                self.idle(event.time - self.cycles)
        else:
            self.idle(1)

    def process_events(self):
        while self.events:
            event = self.events[0]
            if self.cycles >= event.time:
                heapq.heappop(self.events)
                if not event.cancelled:
                    event.callback()
            else:
                break
