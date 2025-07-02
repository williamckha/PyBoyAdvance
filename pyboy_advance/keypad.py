from enum import IntFlag, auto

from pyboy_advance.app.window import WindowEvent
from pyboy_advance.interrupt_controller import InterruptController, Interrupt
from pyboy_advance.utils import bint, get_bit, get_bits


class Key(IntFlag):
    # fmt: off
    BUTTON_A        = auto()
    BUTTON_B        = auto()
    BUTTON_SELECT   = auto()
    BUTTON_START    = auto()
    DPAD_RIGHT      = auto()
    DPAD_LEFT       = auto()
    DPAD_UP         = auto()
    DPAD_DOWN       = auto()
    SHOULDER_RIGHT  = auto()
    SHOULDER_LEFT   = auto()
    # fmt: on


class Keypad:
    def __init__(self, interrupt_controller: InterruptController):
        self.interrupt_controller = interrupt_controller

        # Initialize all keys to "released" state (inputs are active low)
        self.key_input = 0
        for key in Key:
            self.key_input |= key

        self.key_control = KeypadInterruptControlRegister()

    def press_key(self, key: Key):
        self.key_input &= ~key

        if self.key_control.irq_enable and self._evaluate_irq_condition():
            self.interrupt_controller.signal(Interrupt.KEYPAD)

    def release_key(self, key: Key):
        self.key_input |= key

        if self.key_control.irq_enable and self._evaluate_irq_condition():
            self.interrupt_controller.signal(Interrupt.KEYPAD)

    def process_window_event(self, event: WindowEvent):
        if event == WindowEvent.PRESS_BUTTON_A:
            self.press_key(Key.BUTTON_A)
        elif event == WindowEvent.PRESS_BUTTON_B:
            self.press_key(Key.BUTTON_B)
        elif event == WindowEvent.PRESS_BUTTON_SELECT:
            self.press_key(Key.BUTTON_SELECT)
        elif event == WindowEvent.PRESS_BUTTON_START:
            self.press_key(Key.BUTTON_START)
        elif event == WindowEvent.PRESS_DPAD_RIGHT:
            self.press_key(Key.DPAD_RIGHT)
        elif event == WindowEvent.PRESS_DPAD_LEFT:
            self.press_key(Key.DPAD_LEFT)
        elif event == WindowEvent.PRESS_DPAD_UP:
            self.press_key(Key.DPAD_UP)
        elif event == WindowEvent.PRESS_DPAD_DOWN:
            self.press_key(Key.DPAD_DOWN)
        elif event == WindowEvent.PRESS_SHOULDER_RIGHT:
            self.press_key(Key.SHOULDER_RIGHT)
        elif event == WindowEvent.PRESS_SHOULDER_LEFT:
            self.press_key(Key.SHOULDER_LEFT)
        elif event == WindowEvent.RELEASE_BUTTON_A:
            self.release_key(Key.BUTTON_A)
        elif event == WindowEvent.RELEASE_BUTTON_B:
            self.release_key(Key.BUTTON_B)
        elif event == WindowEvent.RELEASE_BUTTON_SELECT:
            self.release_key(Key.BUTTON_SELECT)
        elif event == WindowEvent.RELEASE_BUTTON_START:
            self.release_key(Key.BUTTON_START)
        elif event == WindowEvent.RELEASE_DPAD_RIGHT:
            self.release_key(Key.DPAD_RIGHT)
        elif event == WindowEvent.RELEASE_DPAD_LEFT:
            self.release_key(Key.DPAD_LEFT)
        elif event == WindowEvent.RELEASE_DPAD_UP:
            self.release_key(Key.DPAD_UP)
        elif event == WindowEvent.RELEASE_DPAD_DOWN:
            self.release_key(Key.DPAD_DOWN)
        elif event == WindowEvent.RELEASE_SHOULDER_RIGHT:
            self.release_key(Key.SHOULDER_RIGHT)
        elif event == WindowEvent.RELEASE_SHOULDER_LEFT:
            self.release_key(Key.SHOULDER_LEFT)
        else:
            raise ValueError(f"WindowEvent {event.name} is not a key event")

    def _evaluate_irq_condition(self) -> bool:
        if self.key_control.irq_if_all:
            # Logical AND mode; interrupt requested if ALL of selected keys are pressed
            return (~self.key_input & self.key_control.key_select) == self.key_control.key_select
        else:
            # Logical OR mode; interrupt requested if ANY of selected keys are pressed
            return (~self.key_input & self.key_control.key_select) != 0


class KeypadInterruptControlRegister:
    def __init__(self):
        self.reg = 0

    @property
    def key_select(self) -> int:
        return get_bits(self.reg, 0, 9)

    @property
    def irq_enable(self) -> bint:
        return get_bit(self.reg, 14)

    @property
    def irq_if_all(self) -> bint:
        return get_bit(self.reg, 15)
