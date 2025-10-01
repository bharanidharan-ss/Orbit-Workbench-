import reflex as rx
from app.state import UIState, SessionState


def menu_item(
    text: str,
    on_click: rx.event.EventHandler | rx.event.EventSpec | None = None,
    close_menu: bool = True,
) -> rx.Component:
    events = []
    if on_click:
        events.append(on_click)
    if close_menu:
        events.append(UIState.set_active_menu(""))
    return rx.el.button(
        text,
        on_click=events,
        class_name="w-full text-left px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-md transition-colors",
    )


def dropdown_menu(trigger_text: str, items: list[rx.Component]) -> rx.Component:
    is_open = UIState.active_menu == trigger_text.lower()
    return rx.el.div(
        rx.el.button(
            trigger_text,
            rx.icon("chevron-down", size=12),
            on_click=lambda: UIState.toggle_menu(trigger_text.lower()),
            class_name="flex items-center gap-1 px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded-md transition-colors",
        ),
        rx.cond(
            is_open,
            rx.el.div(
                *items,
                class_name="absolute top-full left-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-lg p-1.5 z-20",
            ),
        ),
        class_name="relative",
    )


def header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.icon("orbit", size=24, class_name="text-orange-500"),
                rx.el.h1(
                    "Orbit", class_name="font-bold text-lg text-gray-800 tracking-wider"
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.nav(
                dropdown_menu(
                    "File",
                    [
                        menu_item(
                            "New Session", on_click=UIState.toggle_new_session_modal
                        ),
                        menu_item(
                            "Import Session (.orb)",
                            on_click=UIState.toggle_import_session_modal,
                        ),
                        menu_item(
                            "Export Session (.orb)",
                            on_click=SessionState.export_session,
                        ),
                    ],
                ),
                menu_item("Edit"),
                menu_item("View"),
                dropdown_menu(
                    "Database",
                    [
                        menu_item(
                            "Connect to Database...",
                            on_click=UIState.toggle_connect_db_modal,
                        )
                    ],
                ),
                menu_item("Server"),
                menu_item("Tools"),
                menu_item("Help"),
                class_name="flex items-center gap-1",
            ),
            class_name="flex items-center justify-between w-full",
        ),
        class_name="h-14 px-4 flex items-center border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10",
    )