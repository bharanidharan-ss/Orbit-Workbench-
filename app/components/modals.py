import reflex as rx
from app.state import UIState, DBState, QueryState, SessionState


def _modal_overlay() -> rx.Component:
    return rx.el.div(class_name="fixed inset-0 bg-black/30 z-40")


def _modal_base(
    children: list[rx.Component],
    on_close: rx.event.EventHandler,
    max_w: str = "max-w-lg",
) -> rx.Component:
    return rx.el.div(
        _modal_overlay(),
        rx.el.div(
            rx.el.div(
                rx.el.div(*children, class_name="p-6"),
                rx.el.button(
                    rx.icon("x", size=20),
                    on_click=on_close,
                    class_name="absolute top-3 right-3 text-gray-500 hover:text-gray-800 p-1 rounded-full",
                ),
                class_name=f"relative bg-white rounded-xl shadow-lg w-full {max_w} mx-4",
            ),
            class_name="fixed inset-0 z-50 flex items-center justify-center",
        ),
    )


def new_session_modal() -> rx.Component:
    return rx.cond(
        UIState.show_new_session_modal,
        _modal_base(
            [
                rx.el.h2(
                    "New Session", class_name="text-xl font-bold text-gray-800 mb-4"
                ),
                rx.el.p(
                    "Starting a new session will clear your current workspace. Are you sure you want to continue?",
                    class_name="text-gray-600 mb-6",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=UIState.toggle_new_session_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200",
                    ),
                    rx.el.button(
                        "Create New Session",
                        on_click=[
                            QueryState.new_session,
                            UIState.toggle_new_session_modal,
                        ],
                        class_name="px-4 py-2 text-sm font-medium text-white bg-orange-500 rounded-lg hover:bg-orange-600",
                    ),
                    class_name="flex justify-end gap-3 mt-6",
                ),
            ],
            on_close=UIState.toggle_new_session_modal,
            max_w="max-w-md",
        ),
    )


def import_modal() -> rx.Component:
    return rx.cond(
        UIState.show_import_modal,
        _modal_base(
            [
                rx.el.h2(
                    "Import Dataset", class_name="text-xl font-bold text-gray-800 mb-4"
                ),
                rx.el.div(
                    rx.el.button(
                        "From File",
                        on_click=lambda: UIState.set_import_source_type("file"),
                        class_name=rx.cond(
                            UIState.import_source_type == "file",
                            "px-4 py-2 text-sm font-medium border-b-2 border-orange-500 text-gray-800 bg-white",
                            "px-4 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
                        ),
                    ),
                    rx.el.button(
                        "From URL",
                        on_click=lambda: UIState.set_import_source_type("url"),
                        class_name=rx.cond(
                            UIState.import_source_type == "url",
                            "px-4 py-2 text-sm font-medium border-b-2 border-orange-500 text-gray-800 bg-white",
                            "px-4 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
                        ),
                    ),
                    class_name="flex border-b border-gray-200 mb-4",
                ),
                rx.cond(
                    UIState.import_source_type == "file",
                    rx.el.div(
                        rx.el.div(
                            rx.icon(
                                "cloud_upload", size=32, class_name="text-gray-500"
                            ),
                            rx.el.h3(
                                "Click to upload or drag and drop",
                                class_name="font-medium text-gray-700",
                            ),
                            rx.el.p(
                                "XLS, CSV, JSON (up to 10MB)",
                                class_name="text-sm text-gray-500",
                            ),
                            class_name="text-center",
                        ),
                        class_name="flex items-center justify-center w-full h-48 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50",
                    ),
                    rx.el.div(
                        rx.el.input(
                            placeholder="https://example.com/data.csv",
                            on_change=UIState.set_import_url,
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        class_name="w-full",
                    ),
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=UIState.toggle_import_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200",
                    ),
                    rx.el.button(
                        "Import",
                        class_name="px-4 py-2 text-sm font-medium text-white bg-black rounded-lg hover:bg-gray-800",
                    ),
                    class_name="flex justify-end gap-3 mt-6",
                ),
            ],
            on_close=UIState.toggle_import_modal,
        ),
    )


def _form_input(
    label: str,
    placeholder: str,
    value: rx.Var,
    on_change: rx.event.EventHandler,
    input_type: str = "text",
) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name="text-sm font-medium text-gray-700 mb-1"),
        rx.el.input(
            placeholder=placeholder,
            on_change=on_change,
            type=input_type,
            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
            default_value=value,
        ),
        class_name="mb-4",
    )


def connect_db_modal() -> rx.Component:
    return rx.cond(
        UIState.show_connect_db_modal,
        _modal_base(
            [
                rx.el.h2(
                    "Connect to Database",
                    class_name="text-xl font-bold text-gray-800 mb-6",
                ),
                rx.el.form(
                    rx.el.div(
                        rx.el.label(
                            "Database Type",
                            class_name="text-sm font-medium text-gray-700 mb-1",
                        ),
                        rx.el.select(
                            rx.foreach(
                                DBState.supported_db_types,
                                lambda type: rx.el.option(type, value=type),
                            ),
                            default_value=DBState.db_form_data["db_type"],
                            on_change=lambda value: DBState.set_db_form_value(
                                "db_type", value
                            ),
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        class_name="mb-4",
                    ),
                    _form_input(
                        "Host",
                        "localhost",
                        DBState.db_form_data["host"],
                        lambda value: DBState.set_db_form_value("host", value),
                    ),
                    _form_input(
                        "Port",
                        "3306",
                        DBState.db_form_data["port"],
                        lambda value: DBState.set_db_form_value("port", value),
                    ),
                    _form_input(
                        "Username",
                        "root",
                        DBState.db_form_data["user"],
                        lambda value: DBState.set_db_form_value("user", value),
                    ),
                    _form_input(
                        "Password",
                        "",
                        DBState.db_form_data["password"],
                        lambda value: DBState.set_db_form_value("password", value),
                        input_type="password",
                    ),
                    _form_input(
                        "Database Name",
                        "",
                        DBState.db_form_data["database"],
                        lambda value: DBState.set_db_form_value("database", value),
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            on_click=UIState.toggle_connect_db_modal,
                            class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200",
                        ),
                        rx.el.button(
                            "Connect",
                            on_click=DBState.connect_to_db,
                            is_loading=DBState.is_connecting,
                            class_name="px-4 py-2 text-sm font-medium text-white bg-black rounded-lg hover:bg-gray-800 disabled:opacity-50",
                        ),
                        class_name="flex justify-end gap-3 mt-6",
                    ),
                ),
            ],
            on_close=UIState.toggle_connect_db_modal,
        ),
    )


def import_session_modal() -> rx.Component:
    return rx.cond(
        UIState.show_import_session_modal,
        _modal_base(
            [
                rx.el.h2(
                    "Import Session (.orb)",
                    class_name="text-xl font-bold text-gray-800 mb-4",
                ),
                rx.upload.root(
                    rx.el.div(
                        rx.icon("cloud_upload", size=32, class_name="text-gray-500"),
                        rx.el.h3(
                            "Click to upload or drag and drop",
                            class_name="font-medium text-gray-700 mt-2",
                        ),
                        rx.el.p(
                            "ORB files up to 10MB", class_name="text-sm text-gray-500"
                        ),
                        class_name="text-center",
                    ),
                    id="import-orb-upload",
                    on_drop=SessionState.handle_session_upload(
                        rx.upload_files(upload_id="import-orb-upload")
                    ),
                    class_name="flex items-center justify-center w-full h-48 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 p-4",
                ),
                rx.el.div(
                    rx.el.button(
                        "Close",
                        on_click=UIState.toggle_import_session_modal,
                        class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200",
                    ),
                    class_name="flex justify-end gap-3 mt-6",
                ),
            ],
            on_close=UIState.toggle_import_session_modal,
        ),
    )