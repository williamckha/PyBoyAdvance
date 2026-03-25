from enum import IntEnum


class ALUOpcode(IntEnum):
    AND = 0x0
    EOR = 0x1
    SUB = 0x2
    RSB = 0x3
    ADD = 0x4
    ADC = 0x5
    SBC = 0x6
    RSC = 0x7
    TST = 0x8
    TEQ = 0x9
    CMP = 0xA
    CMN = 0xB
    ORR = 0xC
    MOV = 0xD
    BIC = 0xE
    MVN = 0xF


class DataTransferOpcode(IntEnum):
    STRH = 1  # Store halfword
    LDRD = 2  # Load doubleword
    STRD = 3  # Store doubleword

    LDRH = 1  # Load unsigned halfword
    LDRSB = 2  # Load signed byte
    LDRSH = 3  # Load signed halfword


class MultiplyLongOpcode(IntEnum):
    UMULL = 0b00
    UMLAL = 0b01
    SMULL = 0b10
    SMLAL = 0b11
