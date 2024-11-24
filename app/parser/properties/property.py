__all__ = ["Property"]

from typing import Union

from typing_extensions import TypeAlias

from .bool import BoolProperty
from .bytes import BytesProperty
from .date import DateProperty
from .datetime import DateTimeProperty
from .dict import DictProperty
from .enum_property import EnumProperty
from .float import FloatProperty
from .int import IntProperty
from .list_property import ListProperty
from .model_property import ModelProperty
from .none import NoneProperty
from .str_property import StrProperty
from .time import TimeProperty


Property: TypeAlias = Union[
    BoolProperty,
    BytesProperty,
    DateTimeProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    ListProperty,
    ModelProperty,
    NoneProperty,
    StrProperty,
    DictProperty,
    DateProperty,
    TimeProperty,
]
