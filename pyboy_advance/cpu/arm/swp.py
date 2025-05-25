import cython

from pyboy_advance.cpu.cpu import CPU


def arm_single_data_swap(cpu: CPU, instr: cython.uint):
    return