from array import array
from typing import TypeAlias

bint: TypeAlias = int
"""
This type alias is used to indicate that the value is intended to behave
like a boolean (0 for False, 1 for True) while still being an integer.
Casting to bool has a measurable performance hit, so it is better to avoid
casts and use bint where possible.
"""


def get_bit(num: int, i: int) -> bint:
    return (num >> i) & 1


def get_bits(num: int, start: int, end: int) -> int:
    num_bits = end - start + 1
    mask = (1 << num_bits) - 1
    return (num >> start) & mask


def set_bit(num: int, i: int, bit: bint) -> int:
    return (num & ~(1 << i)) | (bit << i)


def sign_64(num: int) -> bint:
    return get_bit(num, 64)


def sign_32(num: int) -> bint:
    return get_bit(num, 31)


def sign_24(num: int) -> bint:
    return get_bit(num, 23)


def sign_23(num: int) -> bint:
    return get_bit(num, 22)


def sign_16(num: int) -> bint:
    return get_bit(num, 15)


def sign_12(num: int) -> bint:
    return get_bit(num, 11)


def sign_9(num: int) -> bint:
    return get_bit(num, 8)


def sign_8(num: int) -> bint:
    return get_bit(num, 7)


def extend_sign_16(num: int) -> int:
    return num | 0xFFFF0000 if sign_16(num) else num


def extend_sign_8(num: int) -> int:
    return num | 0xFFFFFF00 if sign_8(num) else num


def interpret_signed_64(num: int) -> int:
    return (num - (1 << 64)) if sign_64(num) else num


def interpret_signed_32(num: int) -> int:
    return (num - (1 << 32)) if sign_32(num) else num


def interpret_signed_24(num: int) -> int:
    return (num - (1 << 24)) if sign_24(num) else num


def interpret_signed_23(num: int) -> int:
    return (num - (1 << 23)) if sign_23(num) else num


def interpret_signed_12(num: int) -> int:
    return (num - (1 << 12)) if sign_12(num) else num


def interpret_signed_9(num: int) -> int:
    return (num - (1 << 9)) if sign_9(num) else num


def interpret_signed_8(num: int) -> int:
    return (num - (1 << 8)) if sign_8(num) else num


def add_uint32_to_uint32(op1_uint: int, op2_uint: int) -> int:
    return (op1_uint + op2_uint) & 0xFFFFFFFF


def add_int32_to_uint32(op_uint: int, op_int: int) -> int:
    return (op_uint + op_int) % 0x100000000


def ror_32(num: int, amount: int) -> int:
    """
    Rotate right (ROR)

    :param num: 32-bit unsigned integer to rotate
    :param amount: number of bits to rotate to the right (must be <= 32)
    :return: num rotated right by amount bits
    """
    return ((num >> amount) | (num << (32 - amount))) & 0xFFFFFFFF


def array_read_32(arr: array, address: int) -> int:
    """Read a little-endian 32-bit value from an array of bytes"""
    b0 = arr[address]
    b1 = arr[address + 1]
    b2 = arr[address + 2]
    b3 = arr[address + 3]
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)


def array_read_16(arr: array, address: int) -> int:
    """Read a little-endian 16-bit value from an array of bytes"""
    b0 = arr[address]
    b1 = arr[address + 1]
    return b0 | (b1 << 8)


def array_write_32(arr: array, address: int, value: int):
    """Write a 32-bit value to the given array of bytes in little-endian format"""
    arr[address] = value & 0xFF
    arr[address + 1] = (value >> 8) & 0xFF
    arr[address + 2] = (value >> 16) & 0xFF
    arr[address + 3] = (value >> 24) & 0xFF


def array_write_16(arr: array, address: int, value: int):
    """Write a 16-bit value to the given array of bytes in little-endian format"""
    arr[address] = value & 0xFF
    arr[address + 1] = (value >> 8) & 0xFF
