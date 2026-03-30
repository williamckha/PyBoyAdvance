import pytest

from pyboy_advance.constants import Key


@pytest.mark.rom_url(
    "https://raw.githubusercontent.com/destoer/armwrestler-gba-fixed/master/armwrestler-gba-fixed.gba"
)
def test_armwrestler_arm(emulator, assert_expected_image):
    emulator.frame(20)

    expected_images = [
        "armwrestler_arm_alu_1.png",
        "armwrestler_arm_alu_2.png",
        "armwrestler_arm_load_1.png",
        "armwrestler_arm_load_2.png",
        "armwrestler_arm_ldm_stm.png",
    ]

    for expected_image in expected_images:
        emulator.press_key(Key.BUTTON_START)
        emulator.frame(20)
        emulator.release_key(Key.BUTTON_START)
        emulator.frame(20)
        assert_expected_image(emulator.screen.image, expected_image)


@pytest.mark.rom_url(
    "https://raw.githubusercontent.com/destoer/armwrestler-gba-fixed/master/armwrestler-gba-fixed.gba"
)
def test_armwrestler_thumb(emulator, assert_expected_image):
    emulator.frame(20)

    for _ in range(3):
        emulator.press_key(Key.DPAD_DOWN)
        emulator.frame(20)
        emulator.release_key(Key.DPAD_DOWN)
        emulator.frame(20)

    expected_images = [
        "armwrestler_thumb_alu.png",
        "armwrestler_thumb_ldr_str.png",
        "armwrestler_thumb_ldm_stm.png",
    ]

    for expected_image in expected_images:
        emulator.press_key(Key.BUTTON_START)
        emulator.frame(20)
        emulator.release_key(Key.BUTTON_START)
        emulator.frame(20)
        assert_expected_image(emulator.screen.image, expected_image)
