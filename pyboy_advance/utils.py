def get_bit(num: int, i: int) -> bool:
    return bool((num >> i) & 1)


def get_bits(num: int, start: int, end: int) -> int:
    num_bits = end - start + 1
    mask = (1 << num_bits) - 1
    return (num >> start) & mask


def set_bit(num: int, i: int, bit: bool) -> int:
    return (num & ~(1 << i)) | (bit << i)
