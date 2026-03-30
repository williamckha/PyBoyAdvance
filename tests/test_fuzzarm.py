import pytest


@pytest.mark.rom_url("https://raw.githubusercontent.com/DenSinH/FuzzARM/master/FuzzARM.gba")
def test_fuzzarm(emulator, assert_expected_image):
    emulator.frame(1000)
    assert_expected_image(emulator.screen.image)
