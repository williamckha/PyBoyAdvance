from pyboy_advance.gba import PyBoyAdvance

import pytest

# Corresponds to instruction "idle: b idle"
ARM_IDLE_INSTRUCTION = 0b11101010111111111111111111111110
THUMB_IDLE_INSTRUCTION = 0b1110011111111110

# Register containing failed test ID (or 0 if all tests passed)
ARM_TEST_REGISTER = 12
THUMB_TEST_REGISTER = 7


def run_test_rom(rom: str, test_reg: int):
    gba = PyBoyAdvance(rom, skip_bios=True)

    try:
        while (
            gba.cpu.pipeline[0] != ARM_IDLE_INSTRUCTION
            and gba.cpu.pipeline[0] != THUMB_IDLE_INSTRUCTION
        ):
            gba.step()
    except Exception as e:
        print(f"Was executing test {gba.cpu.regs[test_reg]:03}")
        raise e

    assert gba.cpu.regs[test_reg] == 0, f"Failed test {gba.cpu.regs[test_reg]:03}"


def test_arm():
    run_test_rom("external/gba-tests/arm/arm.gba", ARM_TEST_REGISTER)


@pytest.mark.skip()
def test_bios():
    run_test_rom("external/gba-tests/bios/bios.gba", ARM_TEST_REGISTER)


def test_memory():
    run_test_rom("external/gba-tests/memory/memory.gba", ARM_TEST_REGISTER)


def test_thumb():
    run_test_rom("external/gba-tests/thumb/thumb.gba", THUMB_TEST_REGISTER)
