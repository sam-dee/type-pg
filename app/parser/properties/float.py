from typing import Any, ClassVar, Union

from attrs import define

from .protocol import PropertyProtocol, Value
from ..errors import PropertyError
from ...utils import PythonIdentifier


@define
class FloatProperty(PropertyProtocol):
    """A property of type float"""

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    comment: str | None

    _type_string: ClassVar[str] = "float"

    @classmethod
    def build(
        cls,
        name: str,
        required: bool,
        default: Any,
        python_name: PythonIdentifier,
        comment: str | None,
    ) -> Union["FloatProperty", PropertyError]:
        checked_default = cls.convert_value(default)
        if isinstance(checked_default, PropertyError):
            return checked_default

        return cls(
            name=name,
            required=required,
            default=checked_default,
            python_name=python_name,
            comment=comment,
        )

    @classmethod
    def convert_value(cls, value: Any) -> Value | None | PropertyError:
        if isinstance(value, Value) or value is None:
            return value
        if isinstance(value, str):
            try:
                parsed = float(value)
                return Value(str(parsed))
            except ValueError:
                return PropertyError(f"Invalid float value: {value}")
        if isinstance(value, float):
            return Value(str(value))
        if isinstance(value, int) and not isinstance(value, bool):
            return Value(str(float(value)))
        return PropertyError(f"Cannot convert {value} to a float")
