# This file was auto-generated using `setup.py generate_constants_pyx`
# Generated from pyboy_advance/ppu/constants.py

cpdef enum LayerType:
    BG_0 = 0
    BG_1 = 1
    BG_2 = 2
    BG_3 = 3
    OBJ = 4

cpdef enum WindowIndex:
    WIN_0 = 0
    WIN_1 = 1
    WIN_OBJ = 2
    WIN_OUT = 3

cdef enum:
    DISPLAY_WIDTH = 240
    DISPLAY_HEIGHT = 160
    HBLANK_PIXELS = 68
    VBLANK_LINES = 68
    CYCLES_PIXEL = 4
    SMALL_DISPLAY_WIDTH = 160
    SMALL_DISPLAY_HEIGHT = 128
    MAX_NUM_OBJECTS = 128
    OAM_ENTRY_SIZE = 8
    TILE_MAP_ENTRY_SIZE = 2
    COLOUR_SIZE = 2
    TRANSPARENT_COLOUR = 32768
    OBJ_TILE_SET_OFFSET = 65536
    OBJ_PALETTE_OFFSET = 512
    VRAM_PAGE_OFFSET = 40960
    NUM_PRIMARY_WINDOWS = 2

