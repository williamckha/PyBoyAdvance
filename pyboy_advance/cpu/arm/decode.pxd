from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU, InstrHandler, InstrPattern
from pyboy_advance.cpu.arm.alu cimport arm_alu
from pyboy_advance.cpu.arm.bdt cimport arm_block_data_transfer
from pyboy_advance.cpu.arm.branch cimport arm_branch_exchange, arm_branch
from pyboy_advance.cpu.arm.hwdt cimport arm_halfword_data_transfer
from pyboy_advance.cpu.arm.mul cimport arm_multiply, arm_multiply_long
from pyboy_advance.cpu.arm.psr cimport arm_msr, arm_mrs
from pyboy_advance.cpu.arm.sdt cimport arm_single_data_transfer
from pyboy_advance.cpu.arm.swi cimport arm_software_interrupt
from pyboy_advance.cpu.arm.swp cimport arm_single_data_swap

cdef InstrPattern[12] ARM_PATTERNS

cdef InstrHandler[4096] ARM_LUT

cdef void fill_arm_lut() noexcept

cdef InstrHandler arm_decoder(uint32_t) except NULL
