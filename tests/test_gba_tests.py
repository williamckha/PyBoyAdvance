from pyboy_advance.gba import GBA

# Corresponds to instruction "idle: b idle"
ARM_IDLE_INSTRUCTION = 0b11101010111111111111111111111110
THUMB_IDLE_INSTRUCTION = 0b1110011111111110

# Register containing failed test ID (or 0 if all tests passed)
ARM_TEST_REGISTER = 12
THUMB_TEST_REGISTER = 7


def run_test_rom(rom: str, idle_instr: int, test_reg: int):
    gba = GBA(rom, skip_bios=True)
    while gba.cpu.pipeline[0] != idle_instr:
        gba.step()
    assert gba.cpu.regs[test_reg] == 0, f"Failed test {gba.cpu.regs[test_reg]:03}"


def test_arm():
    run_test_rom(
        "external/gba-tests/arm/arm.gba",
        ARM_IDLE_INSTRUCTION,
        ARM_TEST_REGISTER
    )


def test_bios():
    run_test_rom(
        "external/gba-tests/bios/bios.gba",
        ARM_IDLE_INSTRUCTION,
        ARM_TEST_REGISTER
    )


def test_memory():
    run_test_rom(
        "external/gba-tests/memory/memory.gba",
        ARM_IDLE_INSTRUCTION,
        ARM_TEST_REGISTER
    )


def test_thumb():
    run_test_rom(
        "external/gba-tests/thumb/thumb.gba",
        THUMB_IDLE_INSTRUCTION,
        THUMB_TEST_REGISTER
    )
