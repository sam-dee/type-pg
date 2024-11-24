from typing import Any, ClassVar, Union

from attrs import define

from ...utils import PythonIdentifier
from ..errors import PropertyError
from .protocol import PropertyProtocol, Value


@define
class BytesProperty(PropertyProtocol):
    """A property of type float"""

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    comment: str | None

    _type_string: ClassVar[str] = "bytes"

    @classmethod
    def build(
        cls,
        name: str,
        required: bool,
        default: Any,
        python_name: PythonIdentifier,
        comment: str | None,
    ) -> Union["BytesProperty", PropertyError]:
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
        if value is not None:
            return PropertyError(detail="ByteProperty cannot have a default value")  # pragma: no cover
        return None
