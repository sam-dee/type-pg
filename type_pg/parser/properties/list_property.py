from typing import Any, ClassVar, Union

from attrs import define

from ...utils import PythonIdentifier
from ..errors import PropertyError
from .protocol import PropertyProtocol, Value


@define
class ListProperty(PropertyProtocol):
    """A property of type str"""

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    inner_property: PropertyProtocol
    comment: str | None
    max_length: int | None

    _type_string: ClassVar[str] = "str"

    @classmethod
    def build(
        cls,
        name: str,
        required: bool,
        default: Any,
        inner_property: PropertyProtocol,
        comment: str | None,
        max_length: int | None,
    ) -> Union["ListProperty", PropertyError]:
        checked_default = cls.convert_value(default)
        if isinstance(checked_default, PropertyError):
            return checked_default
        return cls(
            name=name,
            required=required,
            default=checked_default,
            python_name=PythonIdentifier(value=name, prefix=""),
            inner_property=inner_property,
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

    def get_imports(self, *, prefix: str) -> set[str]:
        """
        Get a set of import strings that should be included when this property is used somewhere

        Args:
            prefix: A prefix to put before any relative (local) module names. This should be the number of . to get
            back to the root of the generated client.
        """
        imports = super().get_imports(prefix=prefix)
        imports.update(self.inner_property.get_imports(prefix=prefix))
        imports.add("from typing import cast, List")
        return imports

    def get_base_type_string(self, *, quoted: bool = False) -> str:
        return f"List[{self.inner_property.get_type_string(quoted=not self.inner_property.is_base_type)}]"

    @classmethod
    def convert_value(cls, value: Any) -> Value | None | PropertyError:
        if value is not None:
            return PropertyError(detail="ListProperty cannot have a default value")  # pragma: no cover
        return None
