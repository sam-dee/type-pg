from typing import Optional, List, TYPE_CHECKING, Union

from attr import Factory
from attrs import define

if TYPE_CHECKING:  # pragma: no cover
    from ...parser import Reference
else:
    Reference = "Reference"


@define
class Column:
    name: str
    type: Union[str, Reference]
    is_nullable: bool
    default: Optional[str]
    max_length: Optional[int]
    comment: Optional[str]
    udt_schema: str
    udt_name: str


@define
class Table:
    schema: str
    name: str
    comment: Optional[str]
    columns: List[Column] = Factory(list)
