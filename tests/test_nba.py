import pytest


@pytest.mark.rom_url(
    "https://raw.githubusercontent.com/nba-emu/hw-test/master/timer/reload/reload.gba"
)
def test_nba_timer_reload(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url(
    "https://raw.githubusercontent.com/nba-emu/hw-test/master/timer/start-stop/start-stop.gba"
)
def test_nba_timer_start_stop(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)
