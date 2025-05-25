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


def ror_32(num: int, amount: int) -> int:
    """
    Rotate right (ROR)

    :param num: 32-bit unsigned integer to rotate
    :param amount: number of bits to rotate to the right (must be <= 32)
    :return: num rotated right by amount bits
    """
    return ((num >> amount) | (num << (32 - amount))) & 0xFFFFFFFF


def compute_shift(num: int, shift: int, shift_carry: bool) -> (int, bool):
    # TODO: implement
    return num
