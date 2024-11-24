from attrs import define

from .protocol import PropertyProtocol
from .types import Class, Types


@define
class EnumProperty(PropertyProtocol):
    class_info: Class
    """A property which represents composite type or table"""
