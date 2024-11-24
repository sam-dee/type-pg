__all__ = ["PropertyProtocol", "Value"]

from abc import abstractmethod
from typing import Any, ClassVar, Protocol

from ...utils import PythonIdentifier
from ..errors import PropertyError


def strip_cast(value: str) -> str:
    return value.split("::")[0]


def is_casted_null(value: str) -> bool:
    return strip_cast(value).lower() in ("'null'", "null")


class Value(str):
    """Represents a valid (converted) value for a property"""


class PropertyProtocol(Protocol):
    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    comment: str | None

    _type_string: ClassVar[str] = ""

    @abstractmethod
    def convert_value(self, value: Any) -> Value | None | PropertyError:
        """Convert a string value to a Value object"""
        raise NotImplementedError()  # pragma: no cover

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
        return f"{self.python_name}: {self.get_type_string(quoted=True)} = Field({default}{comment})"

    def to_function_string(self) -> str:
        """How this should be declared in a (attrs/pydantic)class"""
        default: str | None
        if self.default is not None:
            default = self.default
        elif not self.required:
            default = None
        else:
            default = None

        if default:
            return f"{self.python_name}: {self.get_type_string(quoted=True)} = {default}"
        else:
            return f"{self.python_name}: {self.get_type_string(quoted=True)}"

    def get_base_type_string(self, *, quoted: bool = False) -> str:
        """Get the string describing the Python type of this property. Base types no require quoting."""
        return f'"{self._type_string}"' if not self.is_base_type and quoted else self._type_string

    def get_type_string(
        self,
        no_optional: bool = False,
        *,
        quoted: bool = False,
    ) -> str:
        """
        Get a string representation of type that should be used when declaring this property

        Args:
            no_optional: Do not include Optional or Unset even if the value is optional (needed for isinstance checks)
            json: True if the type refers to the property after JSON serialization
            multipart: True if the type should be used in a multipart request
            quoted: True if the type should be wrapped in quotes (if not a base type)
        """
        type_string = self.get_base_type_string(quoted=quoted)

        if no_optional or self.required:
            return type_string
        return f"Optional[{type_string}]"

    @property
    def is_base_type(self) -> bool:
        """Base types, represented by any other of `Property` than `ModelProperty` should not be quoted."""
        # from . import ListProperty, ModelProperty, UnionProperty
        from . import EnumProperty, ModelProperty

        return self.__class__.__name__ not in {
            ModelProperty.__name__,
            EnumProperty.__name__,
        }

    def get_imports(self, *, prefix: str) -> set[str]:
        """
        Get a set of import strings that should be included when this property is used somewhere

        Args:
            prefix: A prefix to put before any relative (local) module names. This should be the number of . to get
            back to the root of the generated client.
        """
        imports = set()
        if not self.required:
            imports.add("from typing import Optional, cast")
            # imports.add(f"from {prefix}types import UNSET, Unset")
        return imports
