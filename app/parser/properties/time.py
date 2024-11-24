from typing import ClassVar, Any, Union

from attrs import define

from .protocol import PropertyProtocol, Value
from ...utils import PythonIdentifier, FUNCTION_CALL_REGEX
from ..errors import PropertyError
from dateutil.parser import isoparse


@define
class TimeProperty(PropertyProtocol):
    """
    A property of type datetime.time
    """

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    comment: str | None

    _type_string: ClassVar[str] = "datetime.time"

    @classmethod
    def build(
        cls,
        name: str,
        required: bool,
        default: Any,
        python_name: PythonIdentifier,
        comment: str | None,
    ) -> Union["TimeProperty", PropertyError]:
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
            try:
                isoparse(value).date()  # make sure it's a valid value
            except ValueError as e:
                return PropertyError(f"Invalid time: {e}")
            return Value(f"isoparse({value!r}).time()")
        return PropertyError(f"Cannot convert {value} to a time")

    def get_imports(self, *, prefix: str) -> set[str]:
        """
        Get a set of import strings that should be included when this property is used somewhere

        Args:
            prefix: A prefix to put before any relative (local) module names. This should be the number of . to get
            back to the root of the generated client.
        """
        imports = super().get_imports(prefix=prefix)
        imports.update(
            {
                "import datetime",
                "from typing import cast",
                "from dateutil.parser import isoparse",
            }
        )
        return imports
