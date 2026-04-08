cimport cython

from libc.stdint cimport uint32_t, uint64_t

from pyboy_advance.constants cimport EventTrigger

cdef class Event:
    cdef public object callback
    cdef public uint32_t delay
    cdef public uint64_t time
    cdef public bint cancelled

cdef class Scheduler:
    cdef uint64_t cycles
    cdef list events
    cdef dict inactive_events

    @cython.locals(event=Event)
    cdef Event schedule(self, object, uint32_t, EventTrigger) noexcept

    @cython.locals(event=Event)
    cdef void trigger(self, EventTrigger) noexcept

    cdef void idle(self, uint32_t) noexcept

    @cython.locals(event=Event)
    cdef void idle_until_next_event(self) noexcept

    @cython.locals(event=Event)
    cdef void process_events(self) noexcept
