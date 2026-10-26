"""Abstract Syntax Tree node definitions (output of the parser)."""
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


# ---- statements -------------------------------------------------------------
@dataclass
class Program:
    body: List[Any]

@dataclass
class Import:
    items: List[Tuple[List[str], Optional[str]]]
    line: int = 0

@dataclass
class Volume:
    value: Any
    line: int = 0

@dataclass
class Assign:
    name: str
    value: Any
    line: int = 0

@dataclass
class AugAssign:
    name: str
    op: str
    value: Any
    line: int = 0

@dataclass
class Play:
    beat: Any
    start: Optional[Any]
    end: Optional[Any]
    unit: Optional[str]
    is_async: bool = False
    line: int = 0

@dataclass
class Sleep:
    amount: Any
    unit: Optional[str]
    line: int = 0

@dataclass
class For:
    var: str
    iterable: Any
    body: List[Any]
    line: int = 0

@dataclass
class While:
    cond: Any
    body: List[Any]
    line: int = 0

@dataclass
class FuncDef:
    ret_type: str
    name: str
    params: List[str]
    body: List[Any]
    line: int = 0

@dataclass
class Return:
    value: Optional[Any]
    line: int = 0

@dataclass
class CallStmt:
    call: Any
    line: int = 0


# ---- expressions ------------------------------------------------------------
@dataclass
class Num:
    value: Any
    line: int = 0

@dataclass
class Str:
    value: str
    line: int = 0

@dataclass
class ListLit:
    items: List[Any]
    line: int = 0

@dataclass
class Var:
    name: str
    line: int = 0

@dataclass
class Qualified:
    module: str
    sound: str
    line: int = 0

@dataclass
class Index:
    target: Any
    index: Any
    line: int = 0

@dataclass
class Call:
    name: str
    args: List[Any]
    line: int = 0

@dataclass
class BinOp:
    op: str
    left: Any
    right: Any
    line: int = 0

@dataclass
class UnaryMinus:
    operand: Any
    line: int = 0

@dataclass
class Range:
    count: Any
    line: int = 0 
