from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pyboy_advance.interrupt_controller import Interrupt
from pyboy_advance.memory.constants import IOAddress, MemoryAccess
from pyboy_advance.scheduler import Scheduler, EventTrigger
from pyboy_advance.utils import get_bits, bint, get_bit, set_bit

if TYPE_CHECKING:
    from pyboy_advance.memory.memory import Memory


class DMAAddressAdjustment(IntEnum):
    INCREMENT = 0
    DECREMENT = 1
    LEAVE_UNCHANGED = 2
    INCREMENT_RELOAD = 3


class DMATransferSize(IntEnum):
    HALFWORD = 0
    WORD = 1


class DMAStartTiming(IntEnum):
    IMMEDIATELY = 0
    VBLANK = 1
    HBLANK = 2
    SPECIAL = 3


class DMAControlRegister:
    def __init__(self):
        self.reg = 0

    @property
    def dst_address_adjustment(self) -> DMAAddressAdjustment:
        return DMAAddressAdjustment(get_bits(self.reg, 5, 6))

    @property
    def src_address_adjustment(self) -> DMAAddressAdjustment:
        return DMAAddressAdjustment(get_bits(self.reg, 7, 8))

    @property
    def repeat(self) -> bint:
        return get_bit(self.reg, 9)

    @property
    def size(self) -> DMATransferSize:
        return DMATransferSize(get_bit(self.reg, 10))

    @property
    def start_timing(self) -> DMAStartTiming:
        return DMAStartTiming(get_bits(self.reg, 12, 13))

    @property
    def irq_when_done(self) -> bint:
        return get_bit(self.reg, 14)

    @property
    def enable(self) -> bint:
        return get_bit(self.reg, 15)

    @enable.setter
    def enable(self, enable: bint):
        self.reg = set_bit(self.reg, 15, enable)


class DMAChannel:
    SRC_MASK = [0x07FFFFFF, 0x0FFFFFFF, 0x0FFFFFFF, 0x0FFFFFFF]
    DST_MASK = [0x07FFFFFF, 0x07FFFFFF, 0x07FFFFFF, 0x0FFFFFFF]
    COUNT_MASK = [0x3FFF, 0x3FFF, 0x3FFF, 0xFFFF]

    INTERRUPT = [Interrupt.DMA_0, Interrupt.DMA_1, Interrupt.DMA_2, Interrupt.DMA_3]

    TRANSFER_DELAY = 2

    def __init__(self, channel_id: int, scheduler: Scheduler, memory: Memory):
        self.channel_id = channel_id
        self.scheduler = scheduler
        self.memory = memory
        self.fifo = False
        self.pending = False

        self._control_reg = DMAControlRegister()
        self._count = 0
        self._src = 0
        self._dst = 0

        self._internal_src = 0
        self._internal_dst = 0
        self._internal_count = 0

        self._event = None

    @property
    def control_reg(self) -> int:
        return self._control_reg.reg

    @control_reg.setter
    def control_reg(self, value: int) -> None:
        old_enable = self._control_reg.enable
        self._control_reg.reg = value

        if not old_enable and self._control_reg.enable:  # DMA enabled
            self.fifo = (
                self._control_reg.start_timing == DMAStartTiming.SPECIAL
                and (self.channel_id == 1 or self.channel_id == 2)
                and (self._dst == IOAddress.REG_FIFO_A or self._dst == IOAddress.REG_FIFO_B)
            )

            self._internal_src = self._src
            self._internal_dst = self._dst
            self._internal_count = self._count

            # Count of 0 is treated as max count
            if self._internal_count == 0:
                self._internal_count = DMAChannel.COUNT_MASK[self.channel_id] + 1

            if self._control_reg.start_timing == DMAStartTiming.IMMEDIATELY:
                self._event = self.scheduler.schedule(self.activate, DMAChannel.TRANSFER_DELAY)
            elif self._control_reg.start_timing == DMAStartTiming.VBLANK:
                self._event = self.scheduler.schedule(
                    self.activate, DMAChannel.TRANSFER_DELAY, EventTrigger.VBLANK
                )
            elif self._control_reg.start_timing == DMAStartTiming.HBLANK:
                self._event = self.scheduler.schedule(
                    self.activate, DMAChannel.TRANSFER_DELAY, EventTrigger.HBLANK
                )

        elif old_enable and not self._control_reg.enable:  # DMA cancelled
            if self._event:
                self._event.cancelled = False
                self._event = None
            self.pending = False

    @property
    def count(self) -> int:
        return self._count

    @count.setter
    def count(self, value: int) -> None:
        self._count = value & DMAChannel.COUNT_MASK[self.channel_id]

    @property
    def src_address(self) -> int:
        return self._src

    @src_address.setter
    def src_address(self, value: int):
        self._src = value & DMAChannel.SRC_MASK[self.channel_id]

    @property
    def dst_address(self) -> int:
        return self._dst

    @dst_address.setter
    def dst_address(self, value: int):
        self._dst = value & DMAChannel.DST_MASK[self.channel_id]

    def transfer(self):
        if not self.pending:
            return

        transfer_size = self._control_reg.size
        transfer_size_bytes = 4 if transfer_size == DMATransferSize.WORD else 2

        address_alignment = ~0b11 if transfer_size == DMATransferSize.WORD else ~0b1
        self._internal_src &= address_alignment
        self._internal_dst &= address_alignment

        src_adj = self._control_reg.src_address_adjustment
        if src_adj == DMAAddressAdjustment.INCREMENT:
            src_step = transfer_size_bytes
        elif src_adj == DMAAddressAdjustment.DECREMENT:
            src_step = -transfer_size_bytes
        elif src_adj == DMAAddressAdjustment.LEAVE_UNCHANGED:
            src_step = 0
        else:
            raise ValueError

        dst_adj = self._control_reg.dst_address_adjustment
        if self.fifo:
            dst_step = 0
        elif dst_adj == DMAAddressAdjustment.INCREMENT:
            dst_step = transfer_size_bytes
        elif dst_adj == DMAAddressAdjustment.DECREMENT:
            dst_step = -transfer_size_bytes
        elif dst_adj == DMAAddressAdjustment.LEAVE_UNCHANGED:
            dst_step = 0
        elif dst_adj == DMAAddressAdjustment.INCREMENT_RELOAD:
            dst_step = transfer_size_bytes
        else:
            raise ValueError

        access = MemoryAccess.NON_SEQUENTIAL

        for _ in range(self._internal_count):
            if transfer_size == DMATransferSize.WORD:
                value = self.memory.read_32(self._internal_src, access)
                self.memory.write_32(self._internal_dst, value, access)
            else:
                value = self.memory.read_16(self._internal_src, access)
                self.memory.write_16(self._internal_dst, value, access)

            self._internal_src += src_step
            self._internal_dst += dst_step
            access = MemoryAccess.SEQUENTIAL

        if self._control_reg.irq_when_done:
            self.memory.io.interrupt_controller.signal(DMAChannel.INTERRUPT[self.channel_id])

        self.pending = False

        if self._control_reg.repeat:
            if dst_adj == DMAAddressAdjustment.INCREMENT_RELOAD:
                self._internal_dst = self._dst

            if self._control_reg.start_timing == DMAStartTiming.VBLANK:
                self._event = self.scheduler.schedule(
                    self.activate, DMAChannel.TRANSFER_DELAY, EventTrigger.VBLANK
                )
            elif self._control_reg.start_timing == DMAStartTiming.HBLANK:
                self._event = self.scheduler.schedule(
                    self.activate, DMAChannel.TRANSFER_DELAY, EventTrigger.HBLANK
                )
        else:
            self._control_reg.enable = False

    def activate(self):
        if self._control_reg.enable:
            self.pending = True


class DMAController:
    def __init__(self, scheduler: Scheduler, memory: Memory):
        self.channels = [
            DMAChannel(0, scheduler, memory),
            DMAChannel(1, scheduler, memory),
            DMAChannel(2, scheduler, memory),
            DMAChannel(3, scheduler, memory),
        ]

    @property
    def active(self) -> bool:
        return (
            self.channels[0].pending
            or self.channels[1].pending
            or self.channels[2].pending
            or self.channels[3].pending
        )

    def perform_transfers(self):
        for channel in self.channels:
            channel.transfer()