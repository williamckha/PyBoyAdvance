# ifndef CYTHON
from pyboy_advance.ppu.constants import DISPLAY_WIDTH, DISPLAY_HEIGHT
from pyboy_advance.ppu.ppu import PPU
# endif

import ctypes

try:
    import numpy as np
except ImportError:
    np = None

try:
    import PIL.Image as PILImage
except ImportError:
    PILImage = None


class Screen:
    """
    Provides access to the frame buffer of PyBoy Advance.
    """

    def __init__(self, ppu: PPU):
        self.ppu = ppu

    @property
    def ndarray(self) -> "np.ndarray":
        """
        Get the current frame buffer in a NumPy ``ndarray``.

        :return: RGB image in ``ndarray`` of bytes with shape (160, 240, 3)
        """
        buffer_type = ctypes.POINTER(ctypes.c_uint16 * DISPLAY_HEIGHT * DISPLAY_WIDTH)
        buffer = ctypes.cast(self.ppu.frame_buffer_ptr, buffer_type).contents
        img_bgr555 = np.frombuffer(buffer, dtype=np.uint16).reshape((DISPLAY_HEIGHT, DISPLAY_WIDTH))

        # Extract channels
        b = (img_bgr555 >> 10) & 0x1F
        g = (img_bgr555 >> 5) & 0x1F
        r = img_bgr555 & 0x1F

        # Scale 5-bit to 8-bit
        r = (r * 255 // 31).astype(np.uint8)
        g = (g * 255 // 31).astype(np.uint8)
        b = (b * 255 // 31).astype(np.uint8)

        return np.stack([r, g, b], axis=-1)

    @property
    def image(self) -> "PILImage.Image":
        """
        Get a PIL Image of the current frame buffer.

        :return: RGB image of (240, 160) pixels
        """
        return PILImage.fromarray(self.ndarray, "RGB")
