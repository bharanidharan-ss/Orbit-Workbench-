import reflex as rx
from typing import TypedDict, ClassVar, Literal
import duckdb
import pandas as pd
import logging
import asyncio
import re
import uuid
import datetime
import json


class Column(TypedDict):
    """A column in a database table."""

    name: str
    type: str


class Table(TypedDict):
    """A database table."""

    name: str
    columns: list[Column]


class Database(TypedDict):
    """A database with its tables."""

    name: str
    tables: list[Table]


class QueryResult(TypedDict):
    columns: list[str]
    rows: list[list[str | int | float | bool | None]]


class QueryHistoryItem(TypedDict):
    id: str
    natural_language: str
    generated_sql: str
    results: QueryResult
    execution_time: float
    timestamp: str


class _DBConnectionManager:
    """Manages the database connection."""

    _con: ClassVar[duckdb.DuckDBPyConnection | None] = None

    @classmethod
    def get_con(cls):
        """Get the database connection."""
        if cls._con is None:
            cls._con = duckdb.connect(database=":memory:", read_only=False)
        return cls._con

    @classmethod
    def set_con(cls, con):
        """Set the database connection."""
        cls._con = con


DB_SESSION = _DBConnectionManager()


class UIState(rx.State):
    status_text: str = "Not Connected"
    active_editor_tab: str = "query"
    show_import_modal: bool = False
    show_connect_db_modal: bool = False
    show_new_session_modal: bool = False
    show_import_session_modal: bool = False
    import_source_type: Literal["file", "url"] = "file"
    import_url: str = ""
    active_menu: str = ""

    @rx.event
    def toggle_import_modal(self):
        self.show_import_modal = not self.show_import_modal

    @rx.event
    def toggle_connect_db_modal(self):
        self.show_connect_db_modal = not self.show_connect_db_modal

    @rx.event
    def toggle_new_session_modal(self):
        self.show_new_session_modal = not self.show_new_session_modal

    @rx.event
    def toggle_import_session_modal(self):
        self.show_import_session_modal = not self.show_import_session_modal

    @rx.event
    def set_import_source_type(self, type: Literal["file", "url"]):
        self.import_source_type = type

    @rx.event
    def set_import_url(self, url: str):
        self.import_url = url

    @rx.event
    def set_active_editor_tab(self, tab_name: str):
        self.active_editor_tab = tab_name

    @rx.event
    def set_active_menu(self, menu_name: str):
        self.active_menu = menu_name

    @rx.event
    def toggle_menu(self, menu_name: str):
        if self.active_menu == menu_name:
            self.active_menu = ""
        else:
            self.active_menu = menu_name


class DBState(rx.State):
    """The state for managing database connections and schema."""

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
        """Initialize the in-memory database with sample data."""
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
        """Load the schema from the current database connection."""
        con = DB_SESSION.get_con()
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
            if self.schema[0]["tables"]:
                query_state.active_table = self.schema[0]["tables"][0]["name"]

    @rx.event
    def set_db_form_value(self, field: str, value: str):
        """Set a value in the database connection form."""
        self.db_form_data[field] = value

    @rx.event(background=True)
    async def connect_to_db(self):
        """Connect to a database using the form data."""
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


class SessionState(rx.State):
    query_history: list[QueryHistoryItem] = []

    @rx.event
    async def export_session(self) -> rx.event.EventSpec:
        db_state = await self.get_state(DBState)
        session_data = {
            "manifest": {
                "version": "1.0",
                "created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "title": "Orbit Session",
            },
            "connection": db_state.db_form_data,
            "schema_snapshot": db_state.schema,
            "query_history": self.query_history,
        }
        filename = (
            f"orbit-session-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.orb"
        )
        return rx.download(data=json.dumps(session_data, indent=2), filename=filename)

    @rx.event(background=True)
    async def handle_session_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        try:
            file_content = await files[0].read()
            session_data = json.loads(file_content)
            async with self:
                self.query_history = session_data.get("query_history", [])
                db_state = await self.get_state(DBState)
                db_state.db_form_data = session_data.get(
                    "connection", db_state.db_form_data
                )
                db_state.schema = session_data.get("schema_snapshot", db_state.schema)
                query_state = await self.get_state(QueryState)
                if self.query_history:
                    query_state.query_input = self.query_history[-1]["natural_language"]
                ui_state = await self.get_state(UIState)
                ui_state.show_import_session_modal = False
                ui_state.status_text = (
                    f"Successfully imported session from {files[0].filename}"
                )
        except Exception as e:
            logging.exception(f"Failed to import session: {e}")
            async with self:
                ui_state = await self.get_state(UIState)
                ui_state.status_text = f"Error: Failed to import session file."


class QueryState(rx.State):
    query_input: str = 'output("show me all users and their corresponding products")'
    is_running: bool = False
    active_db: str | None = None
    active_table: str | None = None

    @rx.var
    async def active_db_tables(self) -> list[Table]:
        db_state = await self.get_state(DBState)
        if not self.active_db or not db_state.schema:
            return []
        db = next((d for d in db_state.schema if d["name"] == self.active_db), None)
        return db["tables"] if db else []

    @rx.var
    async def er_diagram_markdown(self) -> str:
        db_state = await self.get_state(DBState)
        if not self.active_db:
            return """mermaid
graph TD
    A[Select a database to see ER Diagram]
"""
        db_schema = next(
            (db for db in db_state.schema if db["name"] == self.active_db), None
        )
        if not db_schema:
            return """mermaid
graph TD
    A[Database not found or empty]
"""
        mermaid_string = """erDiagram
"""
        relationships = set()
        table_names = {table["name"] for table in db_schema["tables"]}
        for table in db_schema["tables"]:
            mermaid_string += f"    {table['name']} {{\n"
            for column in table["columns"]:
                mermaid_string += f"        {column['type']} {column['name']}\n"
                if column["name"].endswith("_id") and column["name"] not in [
                    "id",
                    f"{table['name'].rstrip('s')}_id",
                ]:
                    fk_target_table_singular = column["name"].replace("_id", "")
                    fk_target_table_plural = f"{fk_target_table_singular}s"
                    if fk_target_table_plural in table_names:
                        relationships.add(
                            f'''    "{table['name']}" ||--o{{ "{fk_target_table_plural}" : "has"'''
                        )
                    elif fk_target_table_singular in table_names:
                        relationships.add(
                            f'''    "{table['name']}" ||--o{{ "{fk_target_table_singular}" : "has"'''
                        )
            mermaid_string += """    }
"""
        for rel in relationships:
            mermaid_string += f"{rel}\n"
        return f"mermaid\n{mermaid_string}"

    @rx.var
    async def current_results(self) -> QueryResult:
        ss = await self.get_state(SessionState)
        if not ss.query_history:
            return {"columns": [], "rows": []}
        return ss.query_history[-1]["results"]

    @rx.var
    async def last_query_time(self) -> float:
        ss = await self.get_state(SessionState)
        if not ss.query_history:
            return 0.0
        return ss.query_history[-1]["execution_time"]

    @rx.event
    def select_db(self, db_name: str):
        self.active_db = db_name
        self.active_table = None

    @rx.event
    def select_table(self, table_name: str):
        self.active_table = table_name
        self.query_input = f'output("show first 10 rows from {table_name}")'
        return QueryState.run_query

    @rx.event
    def set_query_input(self, value: str):
        self.query_input = value

    @rx.event(background=True)
    async def run_query(self):
        async with self:
            if self.is_running:
                return
            self.is_running = True
            sql_to_run = ""
        start_time = asyncio.get_event_loop().time()
        query_result: QueryResult = {"columns": [], "rows": []}
        status_text = ""
        try:
            match = re.match('output\\("(.*)"\\)', self.query_input.strip())
            if match:
                natural_lang = match.group(1).lower()
                if "all users" in natural_lang and "products" in natural_lang:
                    sql_to_run = "SELECT u.name, u.email, p.name as product_name, p.price FROM users u JOIN sales s ON u.id = s.user_id JOIN products p ON s.product_id = p.product_id;"
                elif "all users" in natural_lang:
                    sql_to_run = "SELECT * FROM users;"
                elif "all products" in natural_lang:
                    sql_to_run = "SELECT * FROM products;"
                elif "all sales" in natural_lang:
                    sql_to_run = "SELECT * FROM sales;"
                elif m := re.match("show first (\\d+) rows from (\\w+)", natural_lang):
                    limit, table = m.groups()
                    sql_to_run = f"SELECT * FROM {table} LIMIT {limit};"
                else:
                    sql_to_run = "SELECT 'Invalid natural language query' as Error;"
            else:
                sql_to_run = self.query_input
            con = DB_SESSION.get_con()
            if con and sql_to_run and ("Invalid" not in sql_to_run):
                result_df = con.execute(sql_to_run).fetchdf()
                query_result = {
                    "columns": result_df.columns.tolist(),
                    "rows": result_df.values.tolist(),
                }
                status_text = f"Success: {len(query_result['rows'])} rows returned."
            else:
                query_result = {
                    "columns": ["Error"],
                    "rows": [["Could not execute query or invalid syntax."]],
                }
                status_text = "Error: Query failed."
        except Exception as e:
            logging.exception(f"Error running query: {e}")
            query_result = {"columns": ["Error"], "rows": [[str(e)]]}
            status_text = f"Error: {e}"
        finally:
            end_time = asyncio.get_event_loop().time()
            query_time = round(end_time - start_time, 2)
            async with self:
                self.is_running = False
                ss = await self.get_state(SessionState)
                ss.query_history.append(
                    {
                        "id": str(uuid.uuid4()),
                        "natural_language": self.query_input,
                        "generated_sql": sql_to_run,
                        "results": query_result,
                        "execution_time": query_time,
                        "timestamp": datetime.datetime.now(
                            datetime.timezone.utc
                        ).isoformat(),
                    }
                )
                ui_state = await self.get_state(UIState)
                ui_state.status_text = status_text

    @rx.event
    async def new_session(self):
        self.query_input = ""
        ss = await self.get_state(SessionState)
        ss.query_history = []
        ui_state = await self.get_state(UIState)
        ui_state.status_text = "New session started."