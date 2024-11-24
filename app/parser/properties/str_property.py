from typing import ClassVar, Any, Union

from attrs import define

from .protocol import PropertyProtocol, Value, is_casted_null, strip_cast
from ..errors import PropertyError
from ...utils import PythonIdentifier, remove_string_escapes


@define
class StrProperty(PropertyProtocol):
    """A property of type str"""

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    comment: str | None
    max_length: int | None

    _type_string: ClassVar[str] = "str"

    @classmethod
    def build(
        cls,
        name: str,
        required: bool,
        default: Any,
        python_name: PythonIdentifier,
        comment: str | None,
        max_length: int | None,
    ) -> Union["StrProperty", PropertyError]:
        checked_default = cls.convert_value(default)
        return cls(
            name=name,
            required=required,
            default=checked_default,
            python_name=python_name,
            comment=comment,
            max_length=max_length,
        )

    def to_string(self) -> str:
        """How this should be declared in a (attrs/pydantic)class"""
        default: str | None
        if self.default is not None:
            default = self.default
        elif not self.required:
            default = "..."
        else:
            default = "..."

        comment = f', title="{self.comment}"' if self.comment else ""
        max_length = f", max_length={self.max_length}" if self.max_length else ""

        return f"{self.python_name}: {self.get_type_string(quoted=True)} = Field({default}{comment}{max_length})"

    @classmethod
    def convert_value(cls, value: Any) -> Value | None:
        if value is None or isinstance(value, Value):
            return value
        if is_casted_null(value):
            return Value("None")
        if not isinstance(value, str):
            value = str(value)
        return Value(repr(strip_cast(remove_string_escapes(value))))
