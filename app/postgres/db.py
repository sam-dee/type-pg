from typing import Optional, List, Dict, Any, TypeAlias

import psycopg
from psycopg.rows import dict_row
from ..config import Config


Row: TypeAlias = Dict[str, Any]
Rows: TypeAlias = List[Row]


class PostgresDB:

    def __init__(self, connection_string: str):
        self.connection_string: str = connection_string
        self.connection = psycopg.connect(self.connection_string, row_factory=dict_row)
        self.cursor = self.connection.cursor()

    def get_schemas(self, config: Config) -> Rows:
        self.cursor.execute(
            """
        select schema_name as name, null as comment from information_schema.schemata
        where schema_name=any(coalesce(%(schema)s, array[schema_name])) and schema_name<>all(coalesce(%(exclude_schemas)s, array[schema_name]))
        and schema_name not ilike 'pg_%%'
        """,
            {"schema": config.schemas, "exclude_schemas": config.exclude_schemas},
        )
        return self.cursor.fetchall()

    def get_tables(self, schema: str | List[str]) -> Rows:
        schemas: List[str] = [schema] if isinstance(schema, str) else schema
        self.cursor.execute(
            """
        select
            table_schema as schema,
            table_name as name,
            obj_description(format('%%s.%%s',table_schema,table_name)::regclass::oid, 'pg_class') as comment
        from information_schema.tables
        where table_schema=any(coalesce(%(schema)s, array[table_schema])) and table_type='BASE TABLE' order by name
        """,
            {"schema": schemas},
        )
        return self.cursor.fetchall()

    def get_table_columns(self, schema: str, table: str) -> Rows:
        self.cursor.execute(
            """
            select
                column_name as name,
                data_type as type,
                is_nullable::bool,
                column_default as "default",
                character_maximum_length as max_length,
                pg_catalog.col_description(format('%%s.%%s',table_schema,table_name)::regclass::oid,ordinal_position) as comment,
                ordinal_position,
                udt_name::regtype,
                udt_schema
            from information_schema.columns
            where table_schema=%(schema)s and table_name=%(table)s
            order by ordinal_position
            """,
            {"schema": schema, "table": table},
        )
        return self.cursor.fetchall()

    def get_object_types(
        self,
        schema: str | List[str],
    ) -> Rows:
        schemas: List[str] = [schema] if isinstance(schema, str) else schema
        self.cursor.execute(
            """
        select
            user_defined_type_schema as schema,
            user_defined_type_name as name,
            null as comment
        from information_schema.user_defined_types
        where user_defined_type_schema=any(coalesce(%(schema)s, array[user_defined_type_schema]))
        """,
            {"schema": schemas},
        )
        return self.cursor.fetchall()

    def get_object_type_attributes(self, schema: str, object_type_name: str) -> Rows:
        self.cursor.execute(
            """
            select
                attribute_name as name,
                data_type as type,
                is_nullable::bool,
                attribute_default as "default",
                character_maximum_length as max_length,
                null as comment,
                ordinal_position,
                attribute_udt_name::regtype as udt_name,
                attribute_udt_schema as udt_schema
            from information_schema.attributes
            where udt_schema=%(schema)s and udt_name=%(object_type_name)s
        """,
            {"schema": schema, "object_type_name": object_type_name},
        )
        return self.cursor.fetchall()

    def get_routines(
        self,
        schema: str | List[str],
    ) -> Rows:
        schemas: List[str] = [schema] if isinstance(schema, str) else schema
        self.cursor.execute(
            """
        select
            routine_schema,
            routine_name as name,
            specific_name,
            data_type as type,
            character_maximum_length as max_length,
            type_udt_schema as udt_schema,
            type_udt_name as udt_name,
            null as comment
        from information_schema.routines
        where routine_schema=any(coalesce(%(schema)s, array[routine_schema])) and routine_type='FUNCTION'
         order by specific_name
        """,
            {"schema": schemas},
        )
        return self.cursor.fetchall()

    def get_routine_parameters(self, schema: str, routine_specific_name: str) -> Rows:
        self.cursor.execute(
            """
            select
                parameter_name as name,
                data_type as type,
                true as is_nullable,
                parameter_default as "default",
                character_maximum_length as max_length,
                null as comment,
                parameter_mode,
                udt_schema,
                case when data_type='ARRAY' then udt_name::regtype::varchar else udt_name end 
            from information_schema.parameters
            where specific_schema=%(schema)s and specific_name=%(routine_specific_name)s order by ordinal_position;
        """,
            {"schema": schema, "routine_specific_name": routine_specific_name},
        )
        return self.cursor.fetchall()

    def __del__(self) -> None:
        self.cursor.close()
        self.connection.close()
