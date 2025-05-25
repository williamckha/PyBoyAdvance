import cython


def get_bit(num: cython.uint, i: cython.uint) -> cython.bint:
    return bool((num >> i) & 1)


def get_bits(num: cython.uint, start: cython.uint, end: cython.uint) -> cython.uint:
    num_bits = end - start + 1
    mask = (1 << num_bits) - 1
    return (num >> start) & mask


def set_bit(num: cython.uint, i: cython.uint, bit: cython.bint) -> cython.uint:
    return (num & ~(1 << i)) | (bit << i)
