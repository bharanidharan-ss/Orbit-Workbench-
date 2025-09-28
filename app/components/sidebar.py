import reflex as rx
from app.states.db_state import DBState, Database, Table
from app.states.query_state import QueryState
from app.states.ui_state import UIState


def schema_item(
    icon_name: str, name: str, is_active: rx.Var[bool], on_click: rx.event.EventHandler
) -> rx.Component:
    return rx.el.button(
        rx.icon(icon_name, size=16, class_name="mr-2 flex-shrink-0 text-gray-500"),
        rx.el.span(name, class_name="truncate text-sm font-medium"),
        on_click=on_click,
        class_name=rx.cond(
            is_active,
            "w-full flex items-center px-2 py-1.5 rounded-md bg-gray-100 text-gray-800",
            "w-full flex items-center px-2 py-1.5 rounded-md text-gray-600 hover:bg-gray-100 hover:text-gray-800",
        ),
    )


def render_table(table: Table) -> rx.Component:
    return schema_item(
        "table",
        table["name"],
        QueryState.active_table == table["name"],
        lambda: QueryState.select_table(table["name"]),
    )


def render_database(db: Database) -> rx.Component:
    is_active_db = QueryState.active_db == db["name"]
    return rx.el.div(
        schema_item(
            "database",
            db["name"],
            is_active_db,
            lambda: QueryState.select_db(db["name"]),
        ),
        rx.cond(
            is_active_db,
            rx.el.div(
                rx.foreach(QueryState.active_db_tables, render_table),
                class_name="pl-4 mt-1 space-y-1",
            ),
        ),
        class_name="w-full",
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.icon("cloud_upload", size=16),
                    "Import Dataset",
                    on_click=UIState.toggle_import_modal,
                    class_name="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-orange-500 rounded-lg hover:bg-orange-600",
                ),
                rx.el.button(
                    rx.icon("database", size=16),
                    "Connect to DB",
                    on_click=UIState.toggle_connect_db_modal,
                    class_name="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200",
                ),
                class_name="grid grid-cols-1 gap-2 mb-4",
            ),
            rx.el.h2(
                "Schemas",
                class_name="px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider",
            ),
            class_name="mb-4",
        ),
        rx.el.div(rx.foreach(DBState.schema, render_database), class_name="space-y-2"),
        class_name="w-64 h-full bg-white border-r border-gray-200 p-4 overflow-y-auto",
    )