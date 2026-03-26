cimport cython

from pyboy_advance.constants cimport EventTrigger

cdef class Event:
    cdef public object callback
    cdef public int delay
    cdef public int time
    cdef public bint cancelled

cdef class Scheduler:
    cdef int cycles
    cdef list events
    cdef dict inactive_events

    @cython.locals(event=Event)
    cdef Event schedule(self, object, int, int)

    @cython.locals(event=Event)
    cdef void trigger(self, int)

    cdef void idle(self, int)

    @cython.locals(event=Event)
    cdef void idle_until_next_event(self)

    @cython.locals(event=Event)
    cdef void process_events(self)
