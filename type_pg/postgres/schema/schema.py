from typing import List, Optional

from attr import Factory
from attrs import define

from .object_type import ObjectType
from .routine import Routine
from .table import Table


@define
class Schema:
    """
    Postgresql schema definition and resources (routines, tables, object types)
    """

    name: str
    comment: Optional[str]
    routines: List[Routine] = Factory(list)
    tables: List[Table] = Factory(list)
    object_types: List[ObjectType] = Factory(list)
