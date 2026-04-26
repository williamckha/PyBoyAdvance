import pytest


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/arm/arm.gba")
def test_jsmolka_arm(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/bios/bios.gba")
def test_jsmolka_bios(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/memory/memory.gba")
def test_jsmolka_memory(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/nes/nes.gba")
def test_jsmolka_nes(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/save/flash64.gba")
def test_jsmolka_save_flash64(emulator, assert_expected_image):
    emulator.frame(80)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/save/flash128.gba")
def test_jsmolka_save_flash128(emulator, assert_expected_image):
    emulator.frame(80)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/save/none.gba")
def test_jsmolka_save_none(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/save/sram.gba")
def test_jsmolka_save_sram(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/thumb/thumb.gba")
def test_jsmolka_thumb(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)


@pytest.mark.skip
@pytest.mark.rom_url("https://raw.githubusercontent.com/jsmolka/gba-tests/master/unsafe/unsafe.gba")
def test_jsmolka_unsafe(emulator, assert_expected_image):
    emulator.frame(20)
    assert_expected_image(emulator.screen.image)
