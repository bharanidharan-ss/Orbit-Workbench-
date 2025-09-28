import reflex as rx
from app.states.ui_state import UIState
from app.states.query_state import QueryState


def status_bar() -> rx.Component:
    return rx.el.footer(
        rx.el.div(
            rx.icon("square_check", size=16, class_name="text-green-500"),
            rx.el.span(UIState.status_text, class_name="truncate"),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.span(f"Query: {QueryState.query_time.to_string()}s"),
            class_name="flex items-center gap-4",
        ),
        class_name="h-10 px-4 flex items-center justify-between border-t border-gray-200 bg-gray-50 text-xs text-gray-600",
    )