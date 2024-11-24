from typing import TYPE_CHECKING, List, Optional, Union

from attr import Factory
from attrs import define

from .table import Column

if TYPE_CHECKING:  # pragma: no cover
    from ...parser import Reference
else:
    Reference = "Reference"


@define
class AnonymousTable:
    name: None = None
    columns: List[Column] = Factory(list)
    comment: None = None


@define
class Parameter:
    name: str
    type: Union[str, Reference]
    is_nullable: bool
    default: Optional[str]
    max_length: Optional[int]
    comment: Optional[str]
    udt_schema: str
    udt_name: str


@define
class Routine:
    schema: str
    name: str
    specific_name: str
    type: Union[str, AnonymousTable, Reference]
    max_length: Optional[int]
    udt_schema: str
    udt_name: str
    comment: Optional[str]
    parameters: List[Parameter] = Factory(list)
    default: None = None
