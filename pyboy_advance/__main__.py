import argparse
import sys

from pyboy_advance.gba import PyBoyAdvance


def main():
    parser = argparse.ArgumentParser("pyboy_advance")
    parser.add_argument("rom", type=str)
    args = parser.parse_args()

    gba = PyBoyAdvance(args.rom, skip_bios=True)
    gba.run()


if __name__ == "__main__":
    sys.exit(main())