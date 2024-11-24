from typing import Any, ClassVar, Union

from attrs import define

from ...utils import PythonIdentifier
from ..errors import PropertyError
from .protocol import PropertyProtocol, Value, is_casted_null


@define
class BoolProperty(PropertyProtocol):
    """Property for bool"""

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    comment: str | None

    _type_string: ClassVar[str] = "bool"

    @classmethod
    def build(
        cls,
        name: str,
        required: bool,
        default: Any,
        python_name: PythonIdentifier,
        comment: str | None,
    ) -> Union["BoolProperty", PropertyError]:
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
            if is_casted_null(value):
                return Value("None")
            if value.lower() == "true":
                return Value("True")
            elif value.lower() == "false":
                return Value("False")
        if isinstance(value, bool):
            return Value(str(value))
        return PropertyError(f"Invalid boolean value: {value}")
