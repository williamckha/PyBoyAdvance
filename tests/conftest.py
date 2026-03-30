import io
import urllib.request
import numpy as np
from pathlib import Path
from zipfile import ZipFile

import pytest
import PIL.Image
import PIL.ImageChops

from pyboy_advance import PyBoyAdvance


def pytest_configure(config):
    config.addinivalue_line("markers", "rom_url: specify URL of test ROM to download")


@pytest.fixture(scope="session")
def pyboy_advance_factory(tmp_path_factory):
    roms_directory = tmp_path_factory.mktemp("roms")

    def download_file(file_name: str, file_url: str) -> Path:
        with urllib.request.urlopen(file_url) as response:
            if file_url.endswith(".zip"):
                with ZipFile(io.BytesIO(response.read()), "r") as zip_file:
                    files = zip_file.namelist()

                    if len(files) != 1:
                        raise ValueError("ZIP does not contain exactly one file")

                    extracted_path = Path(zip_file.extract(files[0], roms_directory))
                    extracted_path.rename(file_name)
                    return extracted_path
            else:
                out_file_path = roms_directory / file_name
                with open(out_file_path, "wb") as out_file:
                    out_file.write(response.read())
                return out_file_path

    bios = download_file(
        "gba_bios.bin",
        "https://raw.githubusercontent.com/Nebuleon/ReGBA/master/bios/gba_bios.bin",
    )

    def make_pyboy_advance(rom_name: str, rom_url: str):
        rom = download_file(rom_name + ".gba", rom_url)
        return PyBoyAdvance(rom, bios=bios, skip_bios=True)

    return make_pyboy_advance


@pytest.fixture
def emulator(request, pyboy_advance_factory):
    test_name = request.node.originalname.removeprefix("test_")

    marker = request.node.get_closest_marker("rom_url")
    if not marker:
        pytest.fail("Please use the rom_url marker to specify a test ROM")
    rom_url = marker.args[0]

    return pyboy_advance_factory(test_name, rom_url)


@pytest.fixture
def assert_expected_image(request, check):
    def _assert_expected_image(img: PIL.Image.Image, expected_img_name: str = None):
        if not expected_img_name:
            test_name = request.node.originalname.removeprefix("test_")
            expected_img_name = test_name + ".png"

        expected_img_file = Path(__file__).parent / "expected" / expected_img_name
        expected_img = PIL.Image.open(expected_img_file) if expected_img_file.is_file() else None

        with check:
            assert expected_img, "No expected image found for this test"

        if not expected_img:
            img.show()
            return

        diff = PIL.ImageChops.difference(img, expected_img)
        assert not diff.getbbox(), "Image did not match expected image"

    return _assert_expected_image
