cimport cython

from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.cpu.arm.constants cimport ALUOpcode
from pyboy_advance.utils cimport get_bits, get_bit, ror_32, sign_32

cdef void arm_alu(CPU, uint32_t) noexcept

cdef void arm_alu(CPU, uint32_t) noexcept

cdef void arm_alu_and(CPU, uint32_t, uint32_t, uint32_t, bint, bint) noexcept

cdef uint32_t arm_alu_and_impl(CPU, uint32_t, uint32_t, uint32_t, bint, bint) noexcept

cdef void arm_alu_eor(CPU, uint32_t, uint32_t, uint32_t, bint, bint) noexcept

cdef uint32_t arm_alu_eor_impl(CPU, uint32_t, uint32_t, uint32_t, bint, bint) noexcept

cdef void arm_alu_sub(CPU, uint32_t, uint32_t, uint32_t, bint) noexcept

@cython.locals(mask=uint32_t)
cdef uint32_t arm_alu_sub_impl(CPU, uint32_t, uint32_t, uint32_t, bint) noexcept

cdef void arm_alu_rsb(CPU, uint32_t, uint32_t, uint32_t, bint) noexcept

cdef void arm_alu_add(CPU, uint32_t, uint32_t, uint32_t, bint) noexcept

@cython.locals(mask=uint32_t)
cdef uint32_t arm_alu_add_impl(CPU, uint32_t, uint32_t, uint32_t, bint) noexcept

@cython.locals(mask=uint32_t)
cdef void arm_alu_adc(CPU, uint32_t, uint32_t, uint32_t, bint) noexcept

@cython.locals(mask=uint32_t)
cdef void arm_alu_sbc(CPU, uint32_t, uint32_t, uint32_t, bint) noexcept

cdef void arm_alu_rsc(CPU, uint32_t, uint32_t, uint32_t, bint) noexcept

cdef void arm_alu_tst(CPU, uint32_t, uint32_t, bint) noexcept

cdef void arm_alu_teq(CPU, uint32_t, uint32_t, bint) noexcept

cdef void arm_alu_cmp(CPU, uint32_t, uint32_t) noexcept

cdef void arm_alu_cmn(CPU, uint32_t, uint32_t) noexcept

cdef void arm_alu_orr(CPU, uint32_t, uint32_t, uint32_t, bint, bint) noexcept

cdef void arm_alu_mov(CPU, uint32_t, uint32_t, bint, bint) noexcept

cdef void arm_alu_bic(CPU, uint32_t, uint32_t, uint32_t, bint, bint) noexcept

@cython.locals(mask=uint32_t)
cdef void arm_alu_mvn(CPU, uint32_t, uint32_t, bint, bint) noexcept
