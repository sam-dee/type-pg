from typing import Dict, List, TYPE_CHECKING, Union

from attr import evolve
from attrs import define, field
from ..errors import ParseError, PropertyError
from ...config import Config

from ...postgres import Table, ObjectType

from ...utils import ClassName, PythonIdentifier


if TYPE_CHECKING:  # pragma: no cover
    from .property import Property
else:
    Property = "Property"


@define(hash=True)
class Reference:
    """
    Reference to table or object type
    """

    schema: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.schema}.{self.name}"


@define
class Class:
    """Represents Python class which will be generated from a table or object type"""

    name: ClassName
    module_name: PythonIdentifier

    @staticmethod
    def from_string(*, string: str, config: Config) -> "Class":
        """Get a Class from an arbitrary string"""
        class_name = string.split("/")[-1]  # Get rid of ref path stuff
        human_class_name = ClassName(class_name, "", humanize=True)
        # override = None  # config.class_overrides.get(class_name)

        class_name = ClassName(class_name, "", humanize=False)
        module_name = PythonIdentifier(class_name, "")

        return Class(name=human_class_name, module_name=module_name)


@define
class Types:
    """
    Structure for containing all defined, shareable, and reusable types (classes and Enums).
    Works like a context
    """

    classes_by_reference: Dict[Reference, Property] = field(factory=dict)
    # dependencies: Dict[Reference, Set[Reference | ClassName]] = field(factory=dict)
    classes_by_name: Dict[ClassName, Property] = field(factory=dict)
    errors: List[ParseError] = field(factory=list)


def update_types_with_data(
    *, ref: Reference, data: Table | ObjectType, types: Types, config: Config
) -> Types | PropertyError:
    """
    Update a `Schemas` using some new reference.

    Args:
        ref: The output of `parse_reference_path` (validated $ref).
        data: The schema of the thing to add to Schemas.
        types: `Types` up until now.
        config: User-provided config for overriding default behavior.

    Returns:
        Either the updated `schemas` input or a `PropertyError` if something went wrong.

    See Also:
        - https://swagger.io/docs/specification/using-ref/
    """
    from . import property_from_data

    prop: Union[PropertyError, Property]
    prop, types = property_from_data(
        data=data,
        name=data.name,
        types=types,
        required=True,
        # parent_name="",
        config=config,
        # Don't process ModelProperty properties because schemas are still being created
        process_properties=False,
        # roots={ref},
    )

    if isinstance(prop, PropertyError):
        return prop

    types = evolve(types, classes_by_reference={ref: prop, **types.classes_by_reference})

    return types
