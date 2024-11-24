__all__ = ["ModelProperty", "EnumProperty", "Property"]

from itertools import chain
from typing import Iterable, List, TypeVar, Union

from attr import evolve

from ... import postgres
from ...config import Config
from ...utils import PythonIdentifier
from ..errors import ParseError, PropertyError
from .bool import BoolProperty
from .bytes import BytesProperty
from .date import DateProperty
from .datetime import DateTimeProperty
from .dict import DictProperty
from .enum_property import EnumProperty
from .float import FloatProperty
from .int import IntProperty
from .list_property import ListProperty
from .model_property import ModelProperty, process_model
from .none import NoneProperty
from .property import Property
from .str_property import StrProperty
from .time import TimeProperty
from .types import Class, Reference, Types, update_types_with_data

T = TypeVar("T")


def parse_type(type: Union[str | Reference, T], udt_schema: str, udt_name: str) -> Union[str | Reference, T]:
    if isinstance(type, Reference):
        return type
    if udt_schema != "pg_catalog":
        return Reference(schema=udt_schema, name=udt_name)
    else:
        return type


def array_type(udt_name: str) -> str | None:
    if "[]" not in udt_name:
        # TODO handle errors!
        return None
    type = udt_name.removesuffix("[]")
    # TODO handle nested arrays!
    if "[]" in type:
        return None
    return type


def _property_from_ref(
    name: str,
    required: bool,
    # parent: oai.Schema | None,
    data: postgres.Column | postgres.Attribute | postgres.Parameter | postgres.Routine,
    types: Types,
    config: Config,
    # roots: set[ReferencePath | utils.ClassName],
) -> tuple[Property | PropertyError, Types]:
    assert isinstance(data.type, Reference)
    existing = types.classes_by_reference.get(data.type)
    if not existing:
        return (
            PropertyError(detail=f'Could not find reference to "{data.type.full_name}" in parsed models or enums'),
            types,
        )

    default = existing.convert_value(data.default)
    if isinstance(default, PropertyError):
        return default, types

    prop = evolve(
        existing,
        required=required,  # type: ignore
        name=name,  # type: ignore
        python_name=PythonIdentifier(value=name, prefix=""),  # type: ignore
        default=default,  # type: ignore
    )

    # types.add_dependencies(ref_path=ref_path, roots=roots)
    return prop, types


def _primitive_property_from_data(
    name: str,
    required: bool,
    data: postgres.Column | postgres.Attribute | postgres.Routine | postgres.Parameter,
) -> Property | PropertyError | None:
    if data.type in ("bigint", "integer"):
        return IntProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )
    if data.type in ("character varying", "text"):
        return StrProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
            data.max_length,
        )
    if data.type in ("timestamp without time zone", "timestamp with time zone"):
        return DateTimeProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )
    if data.type == "date":
        return DateProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )
    if data.type in ("time without time zone", "time with time zone"):
        return TimeProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )
    if data.type == "bytea":
        return BytesProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )
    if data.type in ("numeric", "real", "double precision"):
        return FloatProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )
    if data.type == "boolean":
        return BoolProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )
    if data.type == "void":
        return NoneProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )
    if data.type in ("json", "jsonb"):
        return DictProperty.build(
            name,
            required,
            data.default,
            PythonIdentifier(value=name, prefix=""),
            data.comment,
        )

    return None


def property_from_data(  # noqa: PLR0911
    name: str,
    required: bool,
    data: (
        postgres.Table
        | postgres.ObjectType
        | postgres.Column
        | postgres.Attribute
        | postgres.Routine
        | postgres.Parameter
    ),
    types: Types,
    # parent_name: str,
    config: Config,
    process_properties: bool = True,
    # roots: set[ReferencePath | utils.ClassName] | None = None,
) -> tuple[Property | PropertyError, Types]:
    # may be primitive type, ref to composite type or TODO array
    if isinstance(data, (postgres.Column, postgres.Attribute, postgres.Parameter)):
        data.type = parse_type(data.type, data.udt_schema, data.udt_name)
        if isinstance(data.type, Reference):
            return _property_from_ref(name, required, data, types, config)

        prop = _primitive_property_from_data(name, required, data)
        if prop:
            return prop, types

        element_type = array_type(data.udt_name)
        if element_type:
            data.type = element_type
            prop = _primitive_property_from_data(name, True, data)
            if prop:
                return (
                    ListProperty.build(
                        name,
                        required,
                        None,
                        prop,  # type: ignore
                        data.comment,
                        None,
                    ),
                    types,
                )

    if isinstance(data, (postgres.Table, postgres.ObjectType)):
        return ModelProperty.build(
            data=data,
            name=name,
            types=types,
            required=required,
            config=config,
            process_properties=process_properties,
        )

    if isinstance(data, postgres.Routine):
        dtype = parse_type(data.type, data.udt_schema, data.udt_name)

        # process Reference later
        if isinstance(dtype, str):
            prop = _primitive_property_from_data(name, required, data)
            if prop:
                return prop, types

        prop = None
        if isinstance(data.type, postgres.AnonymousTable):
            prop, _ = ModelProperty.build(
                data=data.type,
                name=name,
                types=types,
                required=True,
                config=config,
                process_properties=process_properties,
            )

            if isinstance(prop, PropertyError):
                return prop, types

        if isinstance(dtype, Reference):
            data.type = dtype
            prop, _ = _property_from_ref(name, True, data, types, config)
            if isinstance(prop, PropertyError):
                return prop, types

        if prop:
            return (
                ListProperty.build(
                    name,
                    True,  # list are always required cause may be empty
                    None,
                    prop,
                    data.comment,
                    None,
                ),
                types,
            )

    return (
        PropertyError(detail=f"Unknown property type, {data.name}, {data.type=}!"),
        types,
    )


def build_types(
    *,
    schemas: List[postgres.Schema],
    types: Types,
    config: Config,
) -> Types:
    """Get a list of Types from an OpenAPI dict"""
    types = _create_types(schemas=schemas, types=types, config=config)
    types = _process_models(types=types, config=config)
    return types


def _create_types(
    *,
    schemas: List[postgres.Schema],
    types: Types,
    config: Config,
) -> Types:
    to_process: Iterable[postgres.Table | postgres.ObjectType] = chain(
        *[s.tables for s in schemas], *[s.object_types for s in schemas]
    )
    still_making_progress = True
    errors: list[PropertyError] = []

    # References may have forward References so keep going as long as we are making progress
    while still_making_progress:
        still_making_progress = False
        errors = []
        next_round = []
        # Only accumulate errors from the last round, since we might fix some along the way
        for data in to_process:
            # if isinstance(data, oai.Reference):
            #     schemas.errors.append(PropertyError(data=data, detail="Reference schemas are not supported."))
            #     continue

            # ref_path = parse_reference_path(f"#/components/schemas/{name}")
            # if isinstance(ref_path, ParseError):
            #     schemas.errors.append(PropertyError(detail=ref_path.detail, data=data))
            #     continue
            ref = Reference(schema=data.schema, name=data.name)
            types_or_err = update_types_with_data(ref=ref, data=data, types=types, config=config)

            if isinstance(types_or_err, PropertyError):
                next_round.append(data)
                errors.append(types_or_err)
                continue

            types = types_or_err
            still_making_progress = True

        to_process = next_round

    types.errors.extend(errors)

    return types


def _process_models(
    *,
    types: Types,
    config: Config,
) -> Types:
    to_process = (prop for prop in types.classes_by_reference.values() if isinstance(prop, ModelProperty))
    still_making_progress = True
    final_model_errors: list[ModelProperty | PropertyError | ParseError] = []
    latest_model_errors: list[ModelProperty | PropertyError | ParseError] = []

    # Models which refer to other models in their allOf must be processed after their referenced models
    while still_making_progress:
        still_making_progress = False
        # Only accumulate errors from the last round, since we might fix some along the way
        latest_model_errors = []
        next_round = []
        for model_prop in to_process:
            types_or_err = process_model(model_prop, types=types, config=config)
            if isinstance(types_or_err, PropertyError):
                latest_model_errors.append(types_or_err)
                next_round.append(model_prop)
                continue
            types = types_or_err
            still_making_progress = True
        to_process = (prop for prop in next_round)

    final_model_errors.extend(latest_model_errors)
    # errors = _process_model_errors(final_model_errors, schemas=schemas)
    types.errors.extend(final_model_errors)  # type: ignore
    return types
