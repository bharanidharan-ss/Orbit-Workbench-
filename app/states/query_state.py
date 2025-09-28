import reflex as rx
from typing import TypedDict
import asyncio
import re
import logging
from app.states.db_state import DB_SESSION, DBState, Table


class QueryResult(TypedDict):
    columns: list[str]
    rows: list[list[str | int | float | bool | None]]


class QueryState(rx.State):
    query_input: str = 'output("show me all users and their corresponding products")'
    is_running: bool = False
    current_results: QueryResult = {"columns": [], "rows": []}
    query_time: float = 0.0
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
        from app.states.ui_state import UIState

        async with self:
            if self.is_running:
                return
            self.is_running = True
            self.current_results = {"columns": [], "rows": []}
            self.query_time = 0.0
            sql_to_run = ""
        start_time = asyncio.get_event_loop().time()
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
                async with self:
                    self.current_results = {
                        "columns": result_df.columns.tolist(),
                        "rows": result_df.values.tolist(),
                    }
                    ui_state = await self.get_state(UIState)
                    ui_state.status_text = (
                        f"Success: {len(self.current_results['rows'])} rows returned."
                    )
            else:
                async with self:
                    self.current_results = {
                        "columns": ["Error"],
                        "rows": [["Could not execute query or invalid syntax."]],
                    }
                    ui_state = await self.get_state(UIState)
                    ui_state.status_text = "Error: Query failed."
        except Exception as e:
            logging.exception(f"Error running query: {e}")
            async with self:
                self.current_results = {"columns": ["Error"], "rows": [[str(e)]]}
                ui_state = await self.get_state(UIState)
                ui_state.status_text = f"Error: {e}"
        finally:
            end_time = asyncio.get_event_loop().time()
            async with self:
                self.is_running = False
                self.query_time = round(end_time - start_time, 2)

    @rx.event
    async def new_session(self):
        from app.states.ui_state import UIState

        self.query_input = ""
        self.current_results = {"columns": [], "rows": []}
        ui_state = await self.get_state(UIState)
        ui_state.status_text = "New session started."