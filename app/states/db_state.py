import reflex as rx
from typing import TypedDict, ClassVar
import duckdb
import pandas as pd
import logging


class Column(TypedDict):
    name: str
    type: str


class Table(TypedDict):
    name: str
    columns: list[Column]


class Database(TypedDict):
    name: str
    tables: list[Table]


class _DBConnectionManager:
    _con: ClassVar[duckdb.DuckDBPyConnection | None] = None

    @classmethod
    def get_con(cls):
        if cls._con is None:
            cls._con = duckdb.connect(database=":memory:", read_only=False)
        return cls._con

    @classmethod
    def set_con(cls, con):
        cls._con = con


DB_SESSION = _DBConnectionManager()


class DBState(rx.State):
    schema: list[Database] = []
    is_connecting: bool = False
    supported_db_types: list[str] = ["duckdb", "mysql", "postgresql", "sqlite"]
    db_form_data: dict[str, str] = {
        "db_type": "duckdb",
        "host": "",
        "port": "",
        "user": "",
        "password": "",
        "database": ":memory:",
    }

    @rx.event(background=True)
    async def initialize_db(self):
        from app.states.ui_state import UIState

        async with self:
            ui_state = await self.get_state(UIState)
            ui_state.status_text = "Initializing in-memory database..."
        con = DB_SESSION.get_con()
        users_df = pd.DataFrame(
            [
                {
                    "id": 1,
                    "name": "Alice",
                    "email": "alice@example.com",
                    "created_at": "2024-01-15 10:00:00",
                },
                {
                    "id": 2,
                    "name": "Bob",
                    "email": "bob@example.com",
                    "created_at": "2024-01-16 11:30:00",
                },
                {
                    "id": 3,
                    "name": "Charlie",
                    "email": "charlie@example.com",
                    "created_at": "2024-01-17 14:00:00",
                },
            ]
        )
        products_df = pd.DataFrame(
            [
                {"product_id": 101, "name": "Laptop", "price": 1200.0, "stock": 50},
                {"product_id": 102, "name": "Mouse", "price": 25.0, "stock": 200},
                {"product_id": 103, "name": "Keyboard", "price": 75.0, "stock": 150},
            ]
        )
        sales_df = pd.DataFrame(
            [
                {
                    "sale_id": 1001,
                    "product_id": 101,
                    "user_id": 1,
                    "amount": 1200.0,
                    "sale_date": "2024-05-01",
                },
                {
                    "sale_id": 1002,
                    "product_id": 102,
                    "user_id": 1,
                    "amount": 25.0,
                    "sale_date": "2024-05-01",
                },
                {
                    "sale_id": 1003,
                    "product_id": 103,
                    "user_id": 2,
                    "amount": 75.0,
                    "sale_date": "2024-05-02",
                },
            ]
        )
        con.execute("CREATE OR REPLACE TABLE users AS SELECT * FROM users_df")
        con.execute("CREATE OR REPLACE TABLE products AS SELECT * FROM products_df")
        con.execute("CREATE OR REPLACE TABLE sales AS SELECT * FROM sales_df")
        async with self:
            ui_state = await self.get_state(UIState)
            ui_state.status_text = "Connected to in-memory DuckDB"
        yield DBState.load_schema

    @rx.event
    async def load_schema(self):
        con = DB_SESSION.get_con()
        from app.states.query_state import QueryState
        from app.states.ui_state import UIState

        self.schema = []
        db_name = "main"
        tables_result = con.execute("SHOW TABLES").fetchall()
        tables = []
        for (table_name,) in tables_result:
            columns_result = con.execute(
                f"PRAGMA table_info('{table_name}')"
            ).fetchall()
            columns = [Column(name=col[1], type=col[2]) for col in columns_result]
            tables.append(Table(name=table_name, columns=columns))
        self.schema.append(Database(name=db_name, tables=tables))
        query_state = await self.get_state(QueryState)
        if self.schema and self.schema[0]["tables"]:
            query_state.active_db = self.schema[0]["name"]
            query_state.active_table = self.schema[0]["tables"][0]["name"]

    @rx.event
    def set_db_form_value(self, field: str, value: str):
        self.db_form_data[field] = value

    @rx.event(background=True)
    async def connect_to_db(self):
        from app.states.ui_state import UIState

        async with self:
            self.is_connecting = True
            ui_state = await self.get_state(UIState)
            ui_state.status_text = f"Connecting to {self.db_form_data['db_type']}..."
        import asyncio

        await asyncio.sleep(1)
        try:
            if self.db_form_data["db_type"] == "duckdb":
                con = duckdb.connect(
                    database=self.db_form_data["database"], read_only=False
                )
                DB_SESSION.set_con(con)
                status = f"Connected to DuckDB file: {self.db_form_data['database']}"
                should_load_schema = True
            else:
                status = f"Successfully connected to {self.db_form_data['db_type']} (Simulated)"
                should_load_schema = False
            async with self:
                ui_state = await self.get_state(UIState)
                ui_state.status_text = status
                ui_state.show_connect_db_modal = False
            if should_load_schema:
                yield DBState.load_schema
        except Exception as e:
            logging.exception(f"Error connecting to DB: {e}")
            async with self:
                ui_state = await self.get_state(UIState)
                ui_state.status_text = f"Connection failed: {e}"
        finally:
            async with self:
                self.is_connecting = False