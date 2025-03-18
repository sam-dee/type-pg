from typing import List

import typer
from .config import Config, validate_config
from type_pg import create_new_client
from typer import Option

app = typer.Typer(pretty_exceptions_enable=False)


@app.command("main")
def main() -> None:
    pass


@app.command("generate")
def generate(
        schemas: List[str] | None = Option(None),
        exclude_schemas: List[str] | None = Option(
            ["information_schema", "public", "pg_catalog", "profile", "dbms_job"]),
        exclude_tables: List[str] | None = Option(None, help="List of tables to exclude"),
        db_host: str = Option(..., help="Hostname or IP address of the database"),
        db_port: str = Option("5432", help="Port of the database"),
        db_name: str = Option(..., help="Name of the database"),
        db_user: str = Option("postgres", help="User of the database"),
        db_password: str = Option("postgres", help="Password for the database user"),
        project_dir: str | None = Option(None, help="Path to project directory (if none use cwd)"),
        async_mode: bool = Option(default=True, help="Generate async client?"),
) -> None:
    config = Config(
        connection_string=f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}",
        database_name=db_name,
        schemas=schemas,
        exclude_schemas=exclude_schemas,
        exclude_tables=exclude_tables or [],
        project_dir=project_dir,
        remove_function_parameter_prefixes=["p"],
        async_mode=async_mode
    )

    errors = validate_config(config)
    if errors:
        print(errors)
        return

    errors = create_new_client(config=config)
    if errors:
        print(errors)
        return
