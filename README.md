<p align="center">
  <img src="https://raw.githubusercontent.com/williamckha/PyBoyAdvance/master/assets/pyboy_advance.svg" alt="PyBoy Advance" width="240">
</p>

---

PyBoy Advance is a Game Boy Advance emulator written in Python.

There are already plenty of fantastic GBA emulators out in the wild,
most written in languages far better suited than Python for emulator development.
This project is not meant to compete with those emulators nor match their
capabilities. In fact, PyBoy Advance is rather crap (and slow!) by comparison. I work on this project purely for fun, 
with my end goal being to offer a highly readable implementation of a GBA emulator for educational purposes.

## Getting started

PyBoy Advance is written in pure Python and technically can be run with the standard CPython interpreter, but
performance will be unacceptably slow. Instead, you will need to run PyBoy Advance with [PyPy](https://pypy.org/),
a fast implementation of Python (see [Downloading and Installing PyPy](https://doc.pypy.org/en/stable/install.html)).

Install PyBoy Advance with `pip`:

```bash
$ pypy -m pip install pyboy-advance
```

You will need to provide a Game Boy Advance BIOS. Normatt's open source BIOS is supported and
available [here](https://github.com/Nebuleon/ReGBA/blob/master/bios/gba_bios.bin).

Launch PyBoy Advance from the terminal:

```bash
$ pyboy_advance --bios /path/to/bios.bin game_rom.gba
```

Or import and use it in your Python scripts:

```python
from pyboy_advance import PyBoyAdvance

emulator = PyBoyAdvance(rom="game_rom.gba", bios="/path/to/bios.bin")
emulator.run()
```

## Screenshots

<p align="center">
  <img src="https://raw.githubusercontent.com/williamckha/PyBoyAdvance/master/assets/screenshot_kirby.png" alt="Screenshot of PyBoy Advance running Kirby: Nightmare in Dream Land" width="400">
</p>

## Acknowledgements

- [GBATEK](https://problemkaputt.de/gbatek.htm) by Martin Korth, the king of GBA hardware documentation
- [ARM7TDMI Technical Reference Manual](https://developer.arm.com/documentation/ddi0210/c/)
- [CowBite Virtual Hardware Specifications](https://www.cs.rit.edu/~tjh8300/CowBite/CowBiteSpec.htm) by Tom Happ
- [Tonc](https://www.coranac.com/tonc/text/toc.htm) by Jasper Vijn
- Excellent reference GBA emulators:
    - [mGBA](https://mgba.io/) by Vicki Pfau (endrift)
    - [NanoBoyAdvance](https://github.com/nba-emu/NanoBoyAdvance) by Fleroviux
    - [Hades](https://github.com/hades-emu/Hades) by Arignir
    - [RustBoyAdvance-NG](https://github.com/michelhe/rustboyadvance-ng/) by Michel Heily
- [GBA Tests](https://github.com/jsmolka/gba-tests) by Julian Smolka
- [PyBoy](https://github.com/Baekalfen/PyBoy) by Mads Ynddal (Baekalfen), a sister project (Game Boy emulator written in
  Python)