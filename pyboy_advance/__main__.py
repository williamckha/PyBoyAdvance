import argparse
import sys

from pyboy_advance.gba import PyBoyAdvance


def main():
    parser = argparse.ArgumentParser("pyboy_advance")
    parser.add_argument("rom", type=str)
    parser.add_argument("--bios", type=str)
    parser.add_argument("--skip-bios", action="store_true")
    args = parser.parse_args()

    pyboy_advance = PyBoyAdvance(args.rom, args.bios, skip_bios=args.skip_bios)
    pyboy_advance.run()


if __name__ == "__main__":
    sys.exit(main())