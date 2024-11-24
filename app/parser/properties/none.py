from typing import Any, ClassVar, Union

from attrs import define

from .protocol import PropertyProtocol, Value
from ...utils import PythonIdentifier
from ..errors import PropertyError


@define
class NoneProperty(PropertyProtocol):
    """A property that can only be None"""

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    comment: str | None

    _type_string: ClassVar[str] = "None"

    @classmethod
    def build(
        cls,
        name: str,
        required: bool,
        default: Any,
        python_name: PythonIdentifier,
        comment: str | None,
    ) -> Union["NoneProperty", PropertyError]:
        checked_default = cls.convert_value(default)
        if isinstance(checked_default, PropertyError):
            return checked_default
        return cls(
            name=name,
            required=True,  # we don't want Optional[None]
            default=checked_default,
            python_name=python_name,
            comment=comment,
        )

    @classmethod
    def convert_value(cls, value: Any) -> Value | None | PropertyError:
        if value is None or isinstance(value, Value):
            return value
        if isinstance(value, str):
            if value == "None":
                return Value(value)
        return PropertyError(f"Value {value} is not valid, only None is allowed")
