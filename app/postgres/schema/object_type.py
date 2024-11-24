from typing import Union, Optional, List, TYPE_CHECKING

from attr import Factory
from attrs import define

if TYPE_CHECKING:  # pragma: no cover
    from ...parser import Reference
else:
    Reference = "Reference"


@define
class Attribute:
    name: str
    type: Union[str, Reference]
    is_nullable: bool
    default: Optional[str]
    max_length: Optional[int]
    comment: Optional[str]
    udt_schema: str
    udt_name: str


@define
class ObjectType:
    """
    Represents a database object type (type or enum)
    """

    schema: str
    name: str
    comment: Optional[str]
    attributes: List[Attribute] = Factory(list)
