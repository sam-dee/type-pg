import re
from typing import List, Optional

from attrs import define


@define
class ConfigError:
    detail: Optional[str] = None
    header: str = "Unable to parse the config"


@define
class Config:
    """Contains all the config values for the generator, from files, defaults, and CLI arguments."""

    connection_string: str
    database_name: str
    schemas: List[str] | None
    exclude_schemas: List[str] | None
    exclude_tables: List[str] | None

    remove_function_parameter_prefixes: List[str] | None

    post_hooks: Optional[List[str]] = [
        "ruff check . --fix --extend-select=I",
        "ruff format .",
        "black .",
        "git add ."
    ]

    project_dir: Optional[str] = None
    async_mode: bool = True


def validate_config(config: Config) -> list[ConfigError]:
    errors: list[ConfigError] = []
    for table in config.exclude_tables:
        if not re.match(r'^\w+\.\w+$', table):
            errors.append(ConfigError(f'Exclude table "table" does not pattern <schema>.<table_name>'))

    return errors
