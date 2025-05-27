from array import array


def get_bit(num: int, i: int) -> bool:
    return bool((num >> i) & 1)


def get_bits(num: int, start: int, end: int) -> int:
    num_bits = end - start + 1
    mask = (1 << num_bits) - 1
    return (num >> start) & mask


def set_bit(num: int, i: int, bit: bool) -> int:
    return (num & ~(1 << i)) | (bit << i)


def sign_32(num: int) -> bool:
    return get_bit(num, 31)


def interpret_signed_24(num: int) -> int:
    return (num - (1 << 24)) if get_bit(num, 23) else num


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
