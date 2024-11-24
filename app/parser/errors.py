from enum import StrEnum
from typing import Optional

__all__ = [
    "ErrorLevel",
    "GeneratorError",
    "ParseError",
    "PropertyError",
]

from attrs import define


class ErrorLevel(StrEnum):
    """The level of an error"""

    WARNING = "WARNING"  # Client is still generated but missing some pieces
    ERROR = "ERROR"  # Client could not be generated


@define
class GeneratorError:
    """Base data struct containing info on an error that occurred"""

    detail: Optional[str] = None
    level: ErrorLevel = ErrorLevel.ERROR
    header: str = "Unable to generate the client"


@define
class ParseError(GeneratorError):
    """An error raised when there's a problem parsing an OpenAPI document"""

    level: ErrorLevel = ErrorLevel.WARNING
    header: str = "Unable to parse this part of your OpenAPI document: "


@define
class PropertyError(ParseError):
    """Error raised when there's a problem creating a Property"""

    header = "Problem creating a Property: "
