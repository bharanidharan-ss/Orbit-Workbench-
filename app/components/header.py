import reflex as rx
from app.states.ui_state import UIState


def menu_item(text: str, on_click: rx.event.EventHandler | None = None) -> rx.Component:
    return rx.el.button(
        text,
        on_click=on_click,
        class_name="px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded-md transition-colors",
    )


def dropdown_menu(trigger_text: str, items: list[rx.Component]) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            trigger_text,
            rx.icon("chevron-down", size=12),
            class_name="flex items-center gap-1 px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded-md transition-colors",
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
                menu_item("File", on_click=UIState.toggle_new_session_modal),
                menu_item("Edit"),
                menu_item("View"),
                menu_item("Database", on_click=UIState.toggle_connect_db_modal),
                menu_item("Server"),
                menu_item("Tools"),
                menu_item("Help"),
                class_name="flex items-center gap-1",
            ),
            class_name="flex items-center justify-between w-full",
        ),
        class_name="h-14 px-4 flex items-center border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10",
    )