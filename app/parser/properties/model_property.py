from typing import Any, List, Union

from attr import evolve
from attrs import define

from .protocol import PropertyProtocol, Value
from ..errors import PropertyError
from ...utils import PythonIdentifier
from .types import Class, Types

from ...postgres import Table, ObjectType, Column, Attribute, AnonymousTable

from ...config import Config


@define
class ModelProperty(PropertyProtocol):
    """A property which represents composite type or table"""

    name: str
    required: bool
    default: Value | None
    python_name: PythonIdentifier
    data: Table | ObjectType | AnonymousTable
    comment: str | None

    class_info: Class
    properties: List["Property"]

    relative_imports: set[str]

    @classmethod
    def build(
        cls,
        *,
        data: Table | ObjectType | AnonymousTable,
        name: str,
        types: Types,
        required: bool,
        config: Config,
        process_properties: bool,
    ) -> tuple[Union["ModelProperty", PropertyError], Types]:
        class_string = data.name or name
        class_info = Class.from_string(string=class_string, config=config)

        properties: list[Property] = []
        relative_imports: set[str] = set()

        prop = ModelProperty(
            name=name,
            required=required,
            default=None,
            python_name=PythonIdentifier(value=name, prefix=""),
            data=data,
            comment=data.comment,
            class_info=class_info,
            properties=properties,
            relative_imports=relative_imports,
        )

        if process_properties:
            types_or_error = process_model(prop, types=types, config=config)
            if isinstance(types_or_error, PropertyError):
                return types_or_error, types

            types = types_or_error

        # if class_info.name in types.classes_by_name:
        #     error = PropertyError(detail=f'Attempted to generate duplicate models with name "{class_info.name}"')
        #     return error, types

        types = evolve(types, classes_by_name={**types.classes_by_name, class_info.name: prop})
        return prop, types

    def get_base_type_string(self, *, quoted: bool = False) -> str:
        return f'"{self.class_info.name}"' if quoted else self.class_info.name

    @classmethod
    def convert_value(cls, value: Any) -> Value | None | PropertyError:
        if value is not None:
            return PropertyError(detail="ModelProperty cannot have a default value")  # pragma: no cover
        return None

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
                "from typing import Dict",
                "from typing import cast",
            }
        )
        if not isinstance(self.data, AnonymousTable):
            imports.add(f"from {prefix}.{self.data.schema} {self.self_import}")

        return imports

    @property
    def self_import(self) -> str:
        """Constructs a self import statement from this ModelProperty's attributes"""
        return f"import {self.class_info.name}"


from .property import Property  # noqa: E402


def process_model(model_prop: ModelProperty, *, types: Types, config: Config) -> Types | PropertyError:
    from . import property_from_data

    """Populate a ModelProperty instance's property data
    Args:
        model_prop: The ModelProperty to build property data for
        schemas: Existing Schemas
        config: Config data for this run of the generator, used to modifying names
    Returns:
        Either the updated `schemas` input or a `PropertyError` if something went wrong.
    """
    properties = []

    attributes_or_columns: List[Attribute] | List[Column]
    if isinstance(model_prop.data, (Table, AnonymousTable)):
        attributes_or_columns = model_prop.data.columns
    else:
        attributes_or_columns = model_prop.data.attributes

    for data in attributes_or_columns:
        prop_or_error, types = property_from_data(data.name, not data.is_nullable, data, types, config, True)
        # accum errors
        if isinstance(prop_or_error, PropertyError):
            return prop_or_error

        imports = prop_or_error.get_imports(prefix="..")
        model_prop.relative_imports.update(prop_or_error.get_imports(prefix=".."))
        properties.append(prop_or_error)

    model_prop.properties = properties
    return types
