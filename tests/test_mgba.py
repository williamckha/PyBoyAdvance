import pytest

from pyboy_advance.constants import Key


def select_test_num(emulator, test_num):
    for _ in range(test_num):
        emulator.press_key(Key.DPAD_DOWN)
        emulator.frame(5)
        emulator.release_key(Key.DPAD_DOWN)
        emulator.frame(5)

    emulator.press_key(Key.BUTTON_A)
    emulator.frame(5)
    emulator.release_key(Key.BUTTON_A)
    emulator.frame(5)


@pytest.mark.skip
@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_memory(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 0)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.skip
@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_io(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 1)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.skip
@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_timing(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 2)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.skip
@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_timer_count_up(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 3)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.skip
@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_timer_irq(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 4)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_shifter(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 5)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_carry(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 6)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.skip
@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_multiply_long(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 7)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.skip
@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_bios(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 8)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.skip
@pytest.mark.rom_url("https://s3.amazonaws.com/mgba/suite-latest.zip")
def test_mgba_dma(emulator, assert_expected_image):
    emulator.frame(20)
    select_test_num(emulator, 9)
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)
