cimport cython

from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.cpu.arm.alu cimport (
    arm_alu_sub,
    arm_alu_add,
    arm_alu_mov,
    arm_alu_adc,
    arm_alu_sbc,
    arm_alu_tst,
    arm_alu_cmp,
    arm_alu_cmn,
    arm_alu_orr,
    arm_alu_bic,
    arm_alu_mvn,
    arm_alu_and,
    arm_alu_eor,
)
from pyboy_advance.cpu.arm.mul cimport arm_multiply_idle
from pyboy_advance.cpu.constants cimport ShiftType
from pyboy_advance.cpu.thumb.constants cimport ThumbALUOpcode
from pyboy_advance.memory.constants cimport MemoryAccess
from pyboy_advance.utils cimport (
    get_bits,
    get_bit,
    sign_32,
    add_32,
)

cdef void thumb_move_shifted_register(CPU, uint32_t) noexcept

cdef void thumb_add_subtract(CPU, uint32_t) noexcept

cdef void thumb_move_compare_add_subtract(CPU, uint32_t) noexcept

cdef void thumb_alu(CPU, uint32_t) noexcept

cdef void thumb_alu_shift(CPU, uint32_t, uint32_t, uint32_t, int) noexcept

@cython.locals(mask=uint32_t)
cdef void thumb_alu_multiply(CPU, uint32_t, uint32_t, uint32_t) noexcept

cdef void thumb_high_reg_branch_exchange(CPU, uint32_t) noexcept

cdef void thumb_add_offset_to_stack_pointer(CPU, uint32_t) noexcept

cdef void thumb_get_address(CPU, uint32_t) noexcept
