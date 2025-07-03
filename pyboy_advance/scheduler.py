import heapq
from dataclasses import dataclass
from typing import Callable


@dataclass
class Event:
    callback: Callable[[], None]
    time: int

    def __lt__(self, other):
        return self.time < other.time


class Scheduler:
    def __init__(self):
        self.events = []
        self.cycles = 0

    def schedule(self, callback: Callable[[], None], time: int):
        heapq.heappush(self.events, Event(callback, self.cycles + time))

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
            event.callback()
