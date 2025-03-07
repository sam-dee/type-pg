__all__ = [
    "Config",
]

import json
import shutil
import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from typing import List, Sequence

from attrs import asdict
from jinja2 import (
    BaseLoader,
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
)

from .config import Config
from .parser import GeneratorData, GeneratorError, Reference
from .parser.database import (
    Class,
    import_string_from_class,
    import_string_from_identifier_and_module,
)
from .parser.errors import ErrorLevel
from .postgres import _get_database
from .utils import ClassName, PythonIdentifier


class Project:
    def __init__(self, *, database: GeneratorData, config: Config) -> None:
        self.database: GeneratorData = database
        self.config: Config = config

        self.project_name: str = "database"
        self.project_dir: Path
        if config.project_dir:
            self.project_dir = Path(config.project_dir)
            if not self.project_dir.exists():
                self.project_dir = Path.cwd()
                # self.errors.append() # TODO: error
        else:
            self.project_dir = Path.cwd()

        self.package_name: str = self.project_name
        self.package_dir: Path = self.project_dir / self.package_name

        package_loader = PackageLoader(__package__)
        loader: BaseLoader = package_loader

        self.env: Environment = Environment(
            loader=loader,
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=["jinja2.ext.loopcontrols"],
            keep_trailing_newline=True,
        )

        self.errors: List[GeneratorError] = []

    def build(self) -> Sequence[GeneratorError]:
        if self.package_dir.is_dir():
            print(f"Removing dir {self.package_dir=}...")
            shutil.rmtree(self.package_dir)

        self._create_package()
        self._build_schemas()
        self._run_post_hooks()

        return self._get_errors()

    def _create_package(self) -> None:
        self.package_dir.mkdir()
        package_init = self.package_dir / "__init__.py"

        imports = []
        alls = []
        for schema_name, schema in self.database.schemas_by_name.items():
            imports.append(f"from . import {schema_name}")
            alls.append(schema_name)

        package_init_template = self.env.get_template("schema_init.py.jinja")
        package_init.write_text(
            package_init_template.render(imports=imports, alls=alls),
            # encoding=self.config.file_encoding,
        )

    def _build_schemas(self) -> None:
        for schema_name, schema in self.database.schemas_by_name.items():
            schema_dir = self.package_dir / schema_name
            schema_dir.mkdir()

            schema_init = schema_dir / "__init__.py"
            schema_imports = []
            schema_alls: list[str | ClassName] = []

            model_template = self.env.get_template("model.py.jinja")

            if schema.tables:
                tables_dir = schema_dir / "tables"
                tables_dir.mkdir()
                tables_init = tables_dir / "__init__.py"

                table_imports = []
                table_alls = []
                for table in schema.tables:
                    module_path = tables_dir / f"{table.class_info.module_name}.py"
                    module_path.write_text(
                        model_template.render(model=table),
                    )
                    table_imports.append(import_string_from_class(table.class_info))
                    table_alls.append(table.class_info.name)

                    schema_imports.append(
                        import_string_from_class(
                            Class(
                                name=table.class_info.name,
                                module_name=PythonIdentifier("tables", ""),
                            )
                        )
                    )
                    schema_alls.append(table.class_info.name)

                tables_init_template = self.env.get_template("schema_init.py.jinja")
                tables_init.write_text(
                    tables_init_template.render(
                        imports=table_imports,
                        alls=table_alls,
                        comment=schema.comment or "",
                    ),
                    # encoding=self.config.file_encoding,
                )

            if schema.object_types:
                object_types_dir = schema_dir / "object_types"
                object_types_dir.mkdir()
                object_types_init = object_types_dir / "__init__.py"

                object_types_imports = []
                object_types_alls = []
                for object_type in schema.object_types:
                    module_path = object_types_dir / f"{object_type.class_info.module_name}.py"
                    module_path.write_text(
                        model_template.render(model=object_type),
                    )
                    object_types_imports.append(import_string_from_class(object_type.class_info))
                    object_types_alls.append(object_type.class_info.name)

                    schema_imports.append(
                        import_string_from_class(
                            Class(
                                name=object_type.class_info.name,
                                module_name=PythonIdentifier("object_types", ""),
                            )
                        )
                    )
                    schema_alls.append(object_type.class_info.name)

                object_types_init_template = self.env.get_template("schema_init.py.jinja")
                object_types_init.write_text(
                    object_types_init_template.render(
                        imports=object_types_imports,
                        alls=object_types_alls,
                        comment=schema.comment or "",
                    ),
                    # encoding=self.config.file_encoding,
                )

            print(f"self.config.async_mode: {self.config.async_mode}")
            if self.config.async_mode:
                routine_template = self.env.get_template("async_routine.py.jinja")

            else:
                routine_template = self.env.get_template("sync_routine.py.jinja")

            if schema.routines:
                routines_dir = schema_dir / "routines"
                routines_dir.mkdir()
                routines_init = routines_dir / "__init__.py"

                routines_imports = []
                routines_alls = []

                for routine in schema.routines:
                    module_path = routines_dir / f"{routine.python_name}.py"
                    # try:
                    module_path.write_text(
                        routine_template.render(routine=routine),
                    )
                    # except Exception as e:
                    #     print(json.dumps(asdict(routine), ensure_ascii=False, default=str))
                    routines_imports.append(
                        import_string_from_identifier_and_module(
                            PythonIdentifier(routine.name, ""),
                            PythonIdentifier(routine.name, ""),
                        )
                    )
                    routines_alls.append(routine.name)

                    schema_imports.append(
                        import_string_from_identifier_and_module(
                            PythonIdentifier(routine.name, ""),
                            PythonIdentifier("routines", ""),
                        )
                    )
                    schema_alls.append(routine.name)

                routines_init_template = self.env.get_template("schema_init.py.jinja")
                routines_init.write_text(
                    routines_init_template.render(
                        imports=routines_imports,
                        alls=routines_alls,
                    ),
                    # encoding=self.config.file_encoding,
                )

            schema_init_template = self.env.get_template("schema_init.py.jinja")
            schema_init.write_text(
                schema_init_template.render(imports=schema_imports, alls=schema_alls),
                # encoding=self.config.file_encoding,
            )

    def _get_errors(self) -> Sequence[GeneratorError]:
        # errors: List[GeneratorError] = []
        return self.errors

    def _run_post_hooks(self) -> None:
        if self.config.post_hooks:
            for command in self.config.post_hooks:
                self._run_command(command)

    def _run_command(self, cmd: str) -> None:
        cmd_name = cmd.split(" ")[0]
        command_exists = shutil.which(cmd_name)
        if not command_exists:
            self.errors.append(
                GeneratorError(
                    level=ErrorLevel.WARNING,
                    header="Skipping Integration",
                    detail=f"{cmd_name} is not in PATH",
                )
            )
            return
        try:
            cwd = (
                self.package_dir
                # if self.config.meta_type == MetaType.NONE
                # else self.project_dir
            )
            subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, check=True)
        except CalledProcessError as err:
            self.errors.append(
                GeneratorError(
                    level=ErrorLevel.ERROR,
                    header=f"{cmd_name} failed",
                    detail=err.stderr.decode() or err.output.decode(),
                )
            )


def _get_project(config: Config) -> Project | GeneratorError:
    data = _get_database(config)
    if isinstance(data, GeneratorError):
        return data
    database = GeneratorData.from_data(data, config=config)

    # print(json.dumps(asdict(database), ensure_ascii=False, default=str))
    if isinstance(database, GeneratorError):
        return database
    return Project(database=database, config=config)


def create_new_client(
    *,
    config: Config,
) -> Sequence[GeneratorError]:
    project = _get_project(
        config=config,
    )
    if isinstance(project, GeneratorError):
        return [project]
    return project.build()
