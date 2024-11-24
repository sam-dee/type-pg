from typing import List, Optional

from attr import Factory
from attrs import define

from .schema import Schema


@define
class Database:
    name: Optional[str]
    schemas: List[Schema] = Factory(list)
