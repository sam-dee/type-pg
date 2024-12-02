from typing import List, Optional

from attrs import define


@define
class Config:
    """Contains all the config values for the generator, from files, defaults, and CLI arguments."""

    connection_string: str
    database_name: str
    schemas: List[str] | None
    exclude_schemas: List[str] | None

    remove_function_parameter_prefixes: List[str] | None

    post_hooks: Optional[List[str]] = [
        "ruff check . --fix",
        "ruff format .",
        "black .",
        "git add ."
    ]

    project_dir: Optional[str] = None
