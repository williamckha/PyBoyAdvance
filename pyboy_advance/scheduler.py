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

    def update(self, cycles: int):
        """
        Update the number of cycles elapsed and process pending events

        :param cycles: number of cycles elapsed since the last scheduler update
        """
        self.cycles += cycles

        if self.events and self.cycles >= self.events[0].time:
            event = heapq.heappop(self.events)
            event.callback()