# ifndef CYTHON
import os
from array import array

from pyboy_advance.memory.constants import (
    MemoryRegion,
    FlashState,
    FlashCommand,
    FlashCommandAddress,
    BackupStorageType,
    FlashManufacturerID,
    FlashDeviceID,
)
# endif


class BackupStorage:
    def __init__(self, backup_storage_type: BackupStorageType):
        self.type = backup_storage_type
        self.sram = array("B", [0xFF] * MemoryRegion.SRAM_SIZE)
        self.flash = Flash(self)

    def read_8(self, address: int) -> int:
        if self.type == BackupStorageType.SRAM:
            return self.sram[address & MemoryRegion.SRAM_MASK]
        elif self.type == BackupStorageType.FLASH_64 or self.type == BackupStorageType.FLASH_128:
            return self.flash.read_8(address)
        elif self.type == BackupStorageType.EEPROM:
            return 0xFF
        else:
            return 0xFF

    def write_8(self, address: int, value: int):
        if self.type == BackupStorageType.SRAM:
            self.sram[address & MemoryRegion.SRAM_MASK] = value
        elif self.type == BackupStorageType.FLASH_64 or self.type == BackupStorageType.FLASH_128:
            self.flash.write_8(address, value)
        elif self.type == BackupStorageType.EEPROM:
            pass

    def save(self, save_file_path: str | os.PathLike):
        with open(save_file_path, "wb") as save_file:
            if self.type == BackupStorageType.SRAM:
                save_file.write(self.sram)
            elif (
                self.type == BackupStorageType.FLASH_64 or self.type == BackupStorageType.FLASH_128
            ):
                save_file.write(self.flash.storage)
            elif self.type == BackupStorageType.EEPROM:
                pass


class Flash:
    def __init__(self, backup_storage: BackupStorage):
        self.backup_storage = backup_storage
        self.storage = array("B", [0xFF] * MemoryRegion.FLASH_128_SIZE)
        self.flash_state = FlashState.READY
        self.identification_mode = False
        self.bank = 0

    def read_8(self, address: int) -> int:
        address &= MemoryRegion.FLASH_MASK

        if self.identification_mode:
            # Use Panasonic for 64K flash and Sanyo for 128K flash
            if address == 0x0:
                return (
                    FlashManufacturerID.PANASONIC
                    if self.backup_storage.type == BackupStorageType.FLASH_64
                    else FlashManufacturerID.SANYO
                )
            elif address == 0x1:
                return (
                    FlashDeviceID.PANASONIC
                    if self.backup_storage.type == BackupStorageType.FLASH_64
                    else FlashDeviceID.SANYO
                )

        return self.storage[address + self.bank * MemoryRegion.FLASH_64_SIZE]

    def write_8(self, address: int, value: int):
        address &= MemoryRegion.FLASH_MASK

        if self.flash_state == FlashState.READY:
            if address == FlashCommandAddress.ADDRESS_1 and value == FlashCommand.UNLOCK_1:
                self.flash_state = FlashState.UNLOCK_1

        elif self.flash_state == FlashState.UNLOCK_1:
            if address == FlashCommandAddress.ADDRESS_2 and value == FlashCommand.UNLOCK_2:
                self.flash_state = FlashState.UNLOCK_2

        elif self.flash_state == FlashState.UNLOCK_2:
            self.flash_state = FlashState.READY
            if address == FlashCommandAddress.ADDRESS_1:
                if value == FlashCommand.ENTER_IDENTIFICATION_MODE:
                    self.identification_mode = True
                elif value == FlashCommand.EXIT_IDENTIFICATION_MODE:
                    self.identification_mode = False
                elif value == FlashCommand.PREPARE_ERASE:
                    self.flash_state = FlashState.ERASE
                elif value == FlashCommand.PREPARE_WRITE:
                    self.flash_state = FlashState.WRITE
                elif value == FlashCommand.SET_BANK:
                    self.flash_state = FlashState.BANK

        elif self.flash_state == FlashState.ERASE:
            if address == FlashCommandAddress.ADDRESS_1 and value == FlashCommand.ERASE_CHIP:
                for i in range(MemoryRegion.FLASH_128_SIZE):
                    self.storage[i] = 0xFF
                self.flash_state = FlashState.READY
            elif (address & ~0xF000) == 0 and value == FlashCommand.ERASE_SECTOR:
                sector_start = address & 0xF000 + self.bank * MemoryRegion.FLASH_64_SIZE
                for i in range(sector_start, sector_start + 0x1000):
                    self.storage[i] = 0xFF
                self.flash_state = FlashState.READY

        elif self.flash_state == FlashState.WRITE:
            self.storage[address + self.bank * MemoryRegion.FLASH_64_SIZE] = value
            self.flash_state = FlashState.READY

        elif self.flash_state == FlashState.BANK:
            if address == 0x0 and (value == 0 or value == 1):
                self.bank = value
                self.flash_state = FlashState.READY
