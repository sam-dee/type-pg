from typing import Any, ClassVar, Union

from attrs import define

from ...utils import FUNCTION_CALL_REGEX, PythonIdentifier
from ..errors import PropertyError
from .protocol import PropertyProtocol, Value, is_casted_null


@define
class IntProperty(PropertyProtocol):
    """A property of type int"""

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    comment: str | None

    _type_string: ClassVar[str] = "int"

    @classmethod
    def build(
        cls,
        name: str,
        required: bool,
        default: Any,
        python_name: PythonIdentifier,
        comment: str | None,
    ) -> Union["IntProperty", PropertyError]:
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
        if value is None or isinstance(value, Value):
            return value
        if isinstance(value, str):
            if FUNCTION_CALL_REGEX.match(value):
                return None
            if is_casted_null(value):
                return Value("None")
            try:
                int(value)
            except ValueError:
                return PropertyError(f"Invalid int value: {value}")
            return Value(value)
        if isinstance(value, int) and not isinstance(value, bool):
            return Value(str(value))
        return PropertyError(f"Invalid int value: {value}")
