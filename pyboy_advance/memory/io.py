from __future__ import annotations

from typing import TYPE_CHECKING

from pyboy_advance.interrupt_controller import InterruptController, PowerDownMode
from pyboy_advance.keypad import Keypad
from pyboy_advance.memory.constants import IOAddress
from pyboy_advance.memory.dma import DMAController
from pyboy_advance.ppu.constants import WindowIndex
from pyboy_advance.ppu.ppu import PPU
from pyboy_advance.utils import get_bit

if TYPE_CHECKING:
    from pyboy_advance.memory.memory import Memory


class IO:
    def __init__(
        self,
        memory: Memory,
        interrupt_controller: InterruptController,
        dma_controller: DMAController,
        ppu: PPU,
        keypad: Keypad,
    ):
        self.memory = memory
        self.interrupt_controller = interrupt_controller
        self.dma_controller = dma_controller
        self.ppu = ppu
        self.keypad = keypad
        self.reg_soundbias = 0

    def read_32(self, address: int) -> int:
        lower_bits = self.read_16(address)
        upper_bits = self.read_16(address + 2)
        return (upper_bits << 16) | lower_bits

    def read_16(self, address: int) -> int:
        # Display Control Registers
        if address == IOAddress.REG_DISPCNT:
            return self.ppu.display_control.reg
        elif address == IOAddress.REG_DISPSTAT:
            return self.ppu.display_status.reg
        elif address == IOAddress.REG_VCOUNT:
            return self.ppu.vcount

        # Background Control Registers
        elif address == IOAddress.REG_BG0CNT:
            return self.ppu.bg_control[0].reg
        elif address == IOAddress.REG_BG1CNT:
            return self.ppu.bg_control[1].reg
        elif address == IOAddress.REG_BG2CNT:
            return self.ppu.bg_control[2].reg
        elif address == IOAddress.REG_BG3CNT:
            return self.ppu.bg_control[3].reg

        # Window Registers
        elif address == IOAddress.REG_WININ:
            win_in = self.ppu.window_control[WindowIndex.WIN_0].reg
            win_in |= self.ppu.window_control[WindowIndex.WIN_1].reg << 8
            return win_in
        elif address == IOAddress.REG_WINOUT:
            win_out = self.ppu.window_control[WindowIndex.WIN_OUT].reg
            win_out |= self.ppu.window_control[WindowIndex.WIN_OBJ].reg << 8
            return win_out

        # Sound Control Registers
        elif address == IOAddress.REG_SOUNDBIAS:
            return self.reg_soundbias

        # DMA Control Registers
        elif address == IOAddress.REG_DMA0CNT_H:
            return self.dma_controller.channels[0].control_reg
        elif address == IOAddress.REG_DMA1CNT_H:
            return self.dma_controller.channels[1].control_reg
        elif address == IOAddress.REG_DMA2CNT_H:
            return self.dma_controller.channels[2].control_reg
        elif address == IOAddress.REG_DMA3CNT_H:
            return self.dma_controller.channels[3].control_reg

        # Keypad Registers
        elif address == IOAddress.REG_KEYINPUT:
            return self.keypad.key_input
        elif address == IOAddress.REG_KEYCNT:
            return self.keypad.key_control.reg

        # Interrupt Registers
        elif address == IOAddress.REG_IE:
            return self.interrupt_controller.interrupt_enable
        elif address == IOAddress.REG_IF:
            return self.interrupt_controller.interrupt_flags
        elif address == IOAddress.REG_WAITCNT:
            return self.memory.wait_control.reg
        elif address == IOAddress.REG_IME:
            return self.interrupt_controller.interrupt_master_enable

        else:
            return 0

    def read_8(self, address: int) -> int:
        value = self.read_16(address & ~1)
        return (value >> ((address & 1) * 8)) & 0xFF

    def write_32(self, address: int, value: int):
        self.write_16(address, value & 0xFFFF)
        self.write_16(address + 2, (value >> 16) & 0xFFFF)

    def write_16(self, address: int, value: int):
        # Display Control Registers
        if address == IOAddress.REG_DISPCNT:
            self.ppu.display_control.reg = value
        elif address == IOAddress.REG_DISPSTAT:
            self.ppu.display_status.reg = value
        elif address == IOAddress.REG_VCOUNT:
            self.ppu.vcount = value

        # Background Control Registers
        elif address == IOAddress.REG_BG0CNT:
            self.ppu.bg_control[0].reg = value
        elif address == IOAddress.REG_BG1CNT:
            self.ppu.bg_control[1].reg = value
        elif address == IOAddress.REG_BG2CNT:
            self.ppu.bg_control[2].reg = value
        elif address == IOAddress.REG_BG3CNT:
            self.ppu.bg_control[3].reg = value

        # Background Offset Registers
        elif address == IOAddress.REG_BG0HOFS:
            self.ppu.bg_offset_h[0] = value & 0x3FF
        elif address == IOAddress.REG_BG0VOFS:
            self.ppu.bg_offset_v[0] = value & 0x3FF
        elif address == IOAddress.REG_BG1HOFS:
            self.ppu.bg_offset_h[1] = value & 0x3FF
        elif address == IOAddress.REG_BG1VOFS:
            self.ppu.bg_offset_v[1] = value & 0x3FF
        elif address == IOAddress.REG_BG2HOFS:
            self.ppu.bg_offset_h[2] = value & 0x3FF
        elif address == IOAddress.REG_BG2VOFS:
            self.ppu.bg_offset_v[2] = value & 0x3FF
        elif address == IOAddress.REG_BG3HOFS:
            self.ppu.bg_offset_h[3] = value & 0x3FF
        elif address == IOAddress.REG_BG3VOFS:
            self.ppu.bg_offset_v[3] = value & 0x3FF

        # Window Registers
        elif address == IOAddress.REG_WIN0H:
            self.ppu.window_h_min[0] = (value >> 8) & 0xFF
            self.ppu.window_h_max[0] = value & 0xFF
        elif address == IOAddress.REG_WIN1H:
            self.ppu.window_h_min[1] = (value >> 8) & 0xFF
            self.ppu.window_h_max[1] = value & 0xFF
        elif address == IOAddress.REG_WIN0V:
            self.ppu.window_v_min[0] = (value >> 8) & 0xFF
            self.ppu.window_v_max[0] = value & 0xFF
        elif address == IOAddress.REG_WIN1V:
            self.ppu.window_v_min[1] = (value >> 8) & 0xFF
            self.ppu.window_v_max[1] = value & 0xFF
        elif address == IOAddress.REG_WININ:
            self.ppu.window_control[WindowIndex.WIN_0].reg = value & 0x3F
            self.ppu.window_control[WindowIndex.WIN_1].reg = (value >> 8) & 0x3F
        elif address == IOAddress.REG_WINOUT:
            self.ppu.window_control[WindowIndex.WIN_OUT].reg = value & 0x3F
            self.ppu.window_control[WindowIndex.WIN_OBJ].reg = (value >> 8) & 0x3F

        # Sound Control Registers
        elif address == IOAddress.REG_SOUNDBIAS:
            self.reg_soundbias = value

        # DMA Source/Destination Registers
        elif address == IOAddress.REG_DMA0SAD_L:
            self.dma_controller.channels[0].src_address &= 0xFFFF0000
            self.dma_controller.channels[0].src_address |= value
        elif address == IOAddress.REG_DMA0SAD_H:
            self.dma_controller.channels[0].src_address &= 0xFFFF
            self.dma_controller.channels[0].src_address |= value << 16
        elif address == IOAddress.REG_DMA0DAD_L:
            self.dma_controller.channels[0].dst_address &= 0xFFFF0000
            self.dma_controller.channels[0].dst_address |= value
        elif address == IOAddress.REG_DMA0DAD_H:
            self.dma_controller.channels[0].dst_address &= 0xFFFF
            self.dma_controller.channels[0].dst_address |= value << 16
        elif address == IOAddress.REG_DMA1SAD_L:
            self.dma_controller.channels[1].src_address &= 0xFFFF0000
            self.dma_controller.channels[1].src_address |= value
        elif address == IOAddress.REG_DMA1SAD_H:
            self.dma_controller.channels[1].src_address &= 0xFFFF
            self.dma_controller.channels[1].src_address |= value << 16
        elif address == IOAddress.REG_DMA1DAD_L:
            self.dma_controller.channels[1].dst_address &= 0xFFFF0000
            self.dma_controller.channels[1].dst_address |= value
        elif address == IOAddress.REG_DMA1DAD_H:
            self.dma_controller.channels[1].dst_address &= 0xFFFF
            self.dma_controller.channels[1].dst_address |= value << 16
        elif address == IOAddress.REG_DMA2SAD_L:
            self.dma_controller.channels[2].src_address &= 0xFFFF0000
            self.dma_controller.channels[2].src_address |= value
        elif address == IOAddress.REG_DMA2SAD_H:
            self.dma_controller.channels[2].src_address &= 0xFFFF
            self.dma_controller.channels[2].src_address |= value << 16
        elif address == IOAddress.REG_DMA2DAD_L:
            self.dma_controller.channels[2].dst_address &= 0xFFFF0000
            self.dma_controller.channels[2].dst_address |= value
        elif address == IOAddress.REG_DMA2DAD_H:
            self.dma_controller.channels[2].dst_address &= 0xFFFF
            self.dma_controller.channels[2].dst_address |= value << 16
        elif address == IOAddress.REG_DMA3SAD_L:
            self.dma_controller.channels[3].src_address &= 0xFFFF0000
            self.dma_controller.channels[3].src_address |= value
        elif address == IOAddress.REG_DMA3SAD_H:
            self.dma_controller.channels[3].src_address &= 0xFFFF
            self.dma_controller.channels[3].src_address |= value << 16
        elif address == IOAddress.REG_DMA3DAD_L:
            self.dma_controller.channels[3].dst_address &= 0xFFFF0000
            self.dma_controller.channels[3].dst_address |= value
        elif address == IOAddress.REG_DMA3DAD_H:
            self.dma_controller.channels[3].dst_address &= 0xFFFF
            self.dma_controller.channels[3].dst_address |= value << 16

        # DMA Control Registers
        elif address == IOAddress.REG_DMA0CNT_L:
            self.dma_controller.channels[0].count = value
        elif address == IOAddress.REG_DMA0CNT_H:
            self.dma_controller.channels[0].control_reg = value
        elif address == IOAddress.REG_DMA1CNT_L:
            self.dma_controller.channels[1].count = value
        elif address == IOAddress.REG_DMA1CNT_H:
            self.dma_controller.channels[1].control_reg = value
        elif address == IOAddress.REG_DMA2CNT_L:
            self.dma_controller.channels[2].count = value
        elif address == IOAddress.REG_DMA2CNT_H:
            self.dma_controller.channels[2].control_reg = value
        elif address == IOAddress.REG_DMA3CNT_L:
            self.dma_controller.channels[3].count = value
        elif address == IOAddress.REG_DMA3CNT_H:
            self.dma_controller.channels[3].control_reg = value

        # Keypad Registers
        elif address == IOAddress.REG_KEYCNT:
            self.keypad.key_control.reg = value

        # Interrupt Registers
        elif address == IOAddress.REG_IE:
            self.interrupt_controller.interrupt_enable = value
        elif address == IOAddress.REG_IF:
            self.interrupt_controller.interrupt_flags = value
        elif address == IOAddress.REG_WAITCNT:
            self.memory.wait_control.reg = value
            self.memory.update_waitstates()
        elif address == IOAddress.REG_IME:
            self.interrupt_controller.interrupt_master_enable = value
        elif address == IOAddress.REG_HALTCNT:
            self.interrupt_controller.power_down_mode = PowerDownMode(get_bit(value, 15) + 1)

    def write_8(self, address: int, value: int):
        aligned_address = address & ~1

        old_value = self.read_16(aligned_address)
        new_value = (
            (old_value & 0x00FF) | (value << 8)
            if get_bit(address, 0)
            else (old_value & 0xFF00) | value
        )

        self.write_16(aligned_address, new_value)
