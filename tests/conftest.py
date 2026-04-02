import functools
import io
import os
import time
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


def pytest_addoption(parser):
    parser.addoption("--bios", action="store")


@pytest.fixture(scope="session")
def bios(pytestconfig):
    bios_path = pytestconfig.getoption("bios")
    if not bios_path:
        pytest.fail("Please provide a BIOS to use with the --bios option")
    return bios_path


@pytest.fixture(scope="session")
def pyboy_advance_factory(tmp_path_factory, bios):
    roms_directory = tmp_path_factory.mktemp("roms")

    @functools.cache
    def download_file(file_url: str) -> Path:
        out_file_name = str(time.time_ns()) + ".gba"
        out_file_path = roms_directory / out_file_name

        with urllib.request.urlopen(file_url) as response:
            if file_url.endswith(".zip"):
                with ZipFile(io.BytesIO(response.read()), "r") as zip_file:
                    files = zip_file.namelist()

                    if len(files) != 1:
                        raise ValueError("ZIP does not contain exactly one file")

                    with zip_file.open(files[0]) as zip_inner_file:
                        with open(out_file_path, "wb") as out_file:
                            out_file.write(zip_inner_file.read())
            else:
                with open(out_file_path, "wb") as out_file:
                    out_file.write(response.read())

        return out_file_path

    def make_pyboy_advance(rom_url: str):
        rom = download_file(rom_url)
        return PyBoyAdvance(rom, bios=bios, skip_bios=True)

    return make_pyboy_advance


@pytest.fixture
def emulator(request, pyboy_advance_factory):
    marker = request.node.get_closest_marker("rom_url")
    if not marker:
        pytest.fail("Please use the rom_url marker to specify a test ROM")
    rom_url = marker.args[0]
    return pyboy_advance_factory(rom_url)


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
        if diff.getbbox():
            artifacts_dir = os.environ.get("PYTEST_ARTIFACTS_DIR", "test_artifacts")
            artifacts_dir_path = Path(os.path.expandvars(artifacts_dir))
            artifacts_dir_path.mkdir(parents=True, exist_ok=True)

            test_id = request.node.nodeid.replace("/", "__").replace("::", "__")
            actual_img_file = artifacts_dir_path / f"{test_id}__actual.png"
            img.save(actual_img_file)

            assert False, f"Image did not match expected image (actual saved at: {actual_img_file})"

    return _assert_expected_image
