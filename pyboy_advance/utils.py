import cython


def get_bit(num: cython.uint, i: cython.uint) -> cython.bint:
    return bool((num >> i) & 1)


def set_bit(num: cython.uint, i: cython.uint, bit: cython.bint) -> cython.uint:
    return (num & ~(1 << i)) | (bit << i)
