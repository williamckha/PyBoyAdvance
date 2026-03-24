# ifndef CYTHON
from dataclasses import dataclass
from typing import Callable, TypeAlias, TYPE_CHECKING

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU

InstrHandler: TypeAlias = Callable[["CPU", int], None]


@dataclass
class InstrPattern:
    mask: int
    value: int
    handler: "InstrHandler"


# endif
