import heapq
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class EventTrigger(Enum):
    IMMEDIATELY = 0
    VBLANK = 1
    HBLANK = 2


@dataclass
class Event:
    callback: Callable[[], None]
    delay: int
    time: int = 0
    cancelled: bool = False

    def __lt__(self, other):
        return self.time < other.time


class Scheduler:
    def __init__(self):
        self.cycles = 0
        self.events = []
        self.inactive_events = defaultdict(list)

    def schedule(
        self,
        callback: Callable[[], None],
        delay: int,
        trigger: EventTrigger = EventTrigger.IMMEDIATELY,
    ) -> Event:
        event = Event(callback, delay)
        if trigger == EventTrigger.IMMEDIATELY:
            event.time = self.cycles + delay
            heapq.heappush(self.events, event)
        else:
            self.inactive_events[trigger].append(event)
        return event

    def trigger(self, trigger: EventTrigger):
        while self.inactive_events[trigger]:
            event = self.inactive_events[trigger].pop()
            event.time = self.cycles + event.delay
            heapq.heappush(self.events, event)

    def idle(self, cycles: int = 1):
        self.cycles += cycles

    def idle_until_next_event(self):
        if self.events and self.events[0].time > self.cycles:
            self.idle(self.events[0].time - self.cycles)
        else:
            self.idle()

    def process_events(self):
        while self.events and self.cycles >= self.events[0].time:
            event = heapq.heappop(self.events)
            if not event.cancelled:
                event.callback()
