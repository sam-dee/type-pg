import json

from attrs import asdict

from .. import Config
from ..parser.errors import GeneratorError
from .db import PostgresDB
from .schema import (
    AnonymousTable,
    Attribute,
    Column,
    Database,
    ObjectType,
    Parameter,
    Routine,
    Schema,
    Table,
)


def _get_database(config: Config) -> Database | GeneratorError:
    db = PostgresDB(config.connection_string)

    schemas = db.get_schemas(config)
    if not schemas:
        return GeneratorError(header="No specified schemas found!")

    database = Database(name=config.database_name)
    for db_schema in schemas:
        schema = Schema(db_schema["name"], db_schema["comment"])
        for db_table in db.get_tables(schema.name):
            table = Table(schema.name, db_table["name"], db_table["comment"])
            for db_table_column in db.get_table_columns(schema.name, table.name):
                column = Column(
                    db_table_column["name"],
                    db_table_column["type"],
                    db_table_column["is_nullable"],
                    db_table_column["default"],
                    db_table_column["max_length"],
                    db_table_column["comment"],
                    db_table_column["udt_schema"],
                    db_table_column["udt_name"],
                )
                table.columns.append(column)
            schema.tables.append(table)
        for db_object_type in db.get_object_types(schema.name):
            object_type = ObjectType(schema.name, db_object_type["name"], db_object_type["comment"])
            for db_object_type_attribute in db.get_object_type_attributes(schema.name, object_type.name):
                attribute = Attribute(
                    db_object_type_attribute["name"],
                    db_object_type_attribute["type"],
                    db_object_type_attribute["is_nullable"],
                    db_object_type_attribute["default"],
                    db_object_type_attribute["max_length"],
                    db_object_type_attribute["comment"],
                    db_object_type_attribute["udt_schema"],
                    db_object_type_attribute["udt_name"],
                )
                object_type.attributes.append(attribute)
            schema.object_types.append(object_type)

        for db_routine in db.get_routines(schema.name):
            routine = Routine(
                schema.name,
                db_routine["name"],
                db_routine["specific_name"],
                db_routine["type"],
                db_routine["max_length"],
                db_routine["udt_schema"],
                db_routine["udt_name"],
                db_routine["comment"],
            )
            return_table = AnonymousTable()
            for db_routine_parameter in db.get_routine_parameters(schema.name, routine.specific_name):
                if "OUT" in db_routine_parameter["parameter_mode"]:
                    column = Column(
                        db_routine_parameter["name"],
                        db_routine_parameter["type"],
                        db_routine_parameter["is_nullable"],
                        db_routine_parameter["default"],
                        db_routine_parameter["max_length"],
                        db_routine_parameter["comment"],
                        db_routine_parameter["udt_schema"],
                        db_routine_parameter["udt_name"],
                    )
                    return_table.columns.append(column)
                if "IN" in db_routine_parameter["parameter_mode"]:
                    routine_parameter = Parameter(
                        db_routine_parameter["name"],
                        db_routine_parameter["type"],
                        db_routine_parameter["is_nullable"],
                        db_routine_parameter["default"],
                        db_routine_parameter["max_length"],
                        db_routine_parameter["comment"],
                        db_routine_parameter["udt_schema"],
                        db_routine_parameter["udt_name"],
                    )
                    routine.parameters.append(routine_parameter)
            if return_table.columns:
                routine.type = return_table
            schema.routines.append(routine)
        # with open(f"{schema.name}.json", "w") as fd:
        # json.dump(asdict(schema), fd, ensure_ascii=False)
        # print(json.dumps(asdict(schema), ensure_ascii=False))

        database.schemas.append(schema)

    return database
