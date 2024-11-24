from typing import Dict, List, Union, Iterable, Set

from attr import Factory, asdict
from attrs import define, field

from . import GeneratorError, ParseError, PropertyError
from .properties import (
    EnumProperty,
    ModelProperty,
    ListProperty,
    Property,
    Types,
    build_types,
    Class,
    property_from_data,
    Reference,
    NoneProperty,
)
from .. import Config
from .. import postgres
from ..utils import PythonIdentifier


def import_string_from_class(class_: Class, prefix: str = "") -> str:
    """Create a string which is used to import a reference"""
    return f"from {prefix}.{class_.module_name} import {class_.name}"


def import_string_from_identifier_and_module(
    identifier: PythonIdentifier, module: PythonIdentifier, prefix: str = ""
) -> str:
    """Create a string which is used to import a reference"""
    return f"from {prefix}.{module} import {identifier}"


def routine_anonymous_table_name(routine: postgres.Routine) -> str:
    return f"return_type"


def remove_function_parameter_prefix(name: str, config: Config) -> str:
    if config.remove_function_parameter_prefixes:
        for prefix in config.remove_function_parameter_prefixes:
            name = name.removeprefix(prefix)
    return name


@define
class RoutineOverload:
    parameters: List[Property]


@define
class Routine:
    schema: str
    name: str
    python_name: PythonIdentifier
    data: postgres.Routine
    parameters: List[Property]
    data_type: Property
    overloads: List[RoutineOverload]
    relative_imports: Set[str] = Factory(set)

    @staticmethod
    def from_data(
        data: postgres.Routine, types: Types, routines: "Routines", config: Config
    ) -> Union["Routine", ParseError]:
        data_type, _ = property_from_data(
            data=data,
            name=routine_anonymous_table_name(data),
            types=types,
            required=False,  # list are always required cause may be empty, primitive types are optional cause may be null
            config=config,
        )

        if isinstance(data_type, PropertyError):
            return ParseError(detail=data_type.detail)

        routine_name = data.name
        ref = Reference(data.schema, routine_name)
        if ref in routines.routine_by_reference:
            routine_name = data.specific_name

        routine = Routine(data.schema, data.name, PythonIdentifier(routine_name, ""), data, [], data_type, [], set())

        # no need to import AnonymousTable
        # if not isinstance(data.type, postgres.AnonymousTable):
        routine.relative_imports.update(data_type.get_imports(prefix=".."))

        for parameter in data.parameters:
            prop, _ = property_from_data(
                data=parameter,
                name=remove_function_parameter_prefix(parameter.name, config),
                types=types,
                required=not parameter.is_nullable,
                config=config,
            )

            if isinstance(prop, PropertyError):
                return ParseError(detail=prop.detail)

            routine.relative_imports.update(prop.get_imports(prefix=".."))

            routine.parameters.append(prop)

        return routine

    @staticmethod
    def add_overload(this_routine: "Routine", other_routine: "Routine") -> Union["Routine", ParseError]:
        this_routine.overloads.append(RoutineOverload(other_routine.parameters))
        return this_routine

    @property
    def is_overloaded(self) -> bool:
        return bool(self.overloads)

    @property
    def returns_anonymous_table(self) -> bool:
        return isinstance(self.data.type, postgres.AnonymousTable)

    @property
    def returns_rows(self) -> bool:
        return isinstance(self.data_type, ListProperty)

    @property
    def returns_none(self) -> bool:
        return isinstance(self.data_type, NoneProperty)

    @property
    def full_name(self) -> str:
        return f"{self.schema}.{self.name}"


@define
class Routines:
    routine_by_reference: Dict[Reference, Routine] = Factory(dict)
    # routine_by_name: Dict[PythonIdentifier, Property] = field(factory=dict)
    errors: List[ParseError] = field(factory=list)

    @staticmethod
    def from_data(data: postgres.Database, types: Types, *, config: Config) -> Union["Routines", GeneratorError]:
        routines = Routines()
        for schema in data.schemas:
            for routine_data in schema.routines:
                routine = Routine.from_data(routine_data, types, routines, config=config)
                if isinstance(routine, ParseError):
                    routines.errors.append(routine)
                    continue
                ref = Reference(schema=routine_data.schema, name=routine.python_name)
                routines.routine_by_reference[ref] = routine

        return routines


@define
class Schema:
    """
    Describes single database schema
    """

    name: str
    comment: str | None
    tables: Iterable[ModelProperty]
    object_types: Iterable[ModelProperty | EnumProperty]
    routines: Iterable[Routine]


@define
class GeneratorData:
    schemas_by_name: Dict[str, Schema]

    @staticmethod
    def from_data(data: postgres.Database, *, config: Config) -> Union["GeneratorData", GeneratorError]:
        types = Types()
        if data.schemas:
            types = build_types(schemas=data.schemas, types=types, config=config)
            print("errors:", types.errors)

        _routines = Routines.from_data(data, types, config=config)
        if isinstance(_routines, GeneratorError):
            return _routines

        print(_routines.errors)

        schemas_by_name: Dict[str, Schema] = {}
        for schema in data.schemas:
            tables = [  # TODO: why () does not work?
                prop
                for ref, prop in types.classes_by_reference.items()
                if isinstance(prop, ModelProperty)
                and ref.schema == schema.name
                and isinstance(prop.data, postgres.Table)
            ]
            object_types = [
                prop
                for ref, prop in types.classes_by_reference.items()
                if isinstance(prop, ModelProperty)
                and ref.schema == schema.name
                and isinstance(prop.data, postgres.ObjectType)
            ]
            routines = [
                routine for ref, routine in _routines.routine_by_reference.items() if ref.schema == schema.name
            ]
            schemas_by_name[schema.name] = Schema(
                name=schema.name,
                comment=schema.comment,
                tables=tables,
                object_types=object_types,
                routines=routines,
            )

        return GeneratorData(schemas_by_name=schemas_by_name)
