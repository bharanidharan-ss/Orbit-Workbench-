import reflex as rx
from reflex_monaco import monaco
from app.state import QueryState, UIState
from app.components.results_table import results_table
from app.components.er_diagram import er_diagram_view


def _tab_button(name: str, tab_key: str) -> rx.Component:
    is_active = UIState.active_editor_tab == tab_key
    return rx.el.button(
        name,
        on_click=lambda: UIState.set_active_editor_tab(tab_key),
        class_name=rx.cond(
            is_active,
            "px-4 py-2 text-sm font-medium border-b-2 border-orange-500 text-gray-800 bg-white",
            "px-4 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
        ),
    )


def query_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                monaco(
                    value=QueryState.query_input,
                    on_change=QueryState.set_query_input,
                    language="sql",
                    theme="vs-light",
                    height="100%",
                    options={
                        "minimap": {"enabled": False},
                        "wordWrap": "on",
                        "fontSize": 14,
                        "lineNumbers": "off",
                    },
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("play", size=16),
                        "Run",
                        on_click=QueryState.run_query,
                        is_loading=QueryState.is_running,
                        class_name="flex items-center gap-2 bg-black text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-800 disabled:opacity-50",
                    ),
                    class_name="absolute bottom-4 right-4 z-10",
                ),
                class_name="relative h-full w-full border border-gray-200 rounded-lg overflow-hidden",
            ),
            class_name="flex h-1/2 p-4 gap-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h2("Results", class_name="text-sm font-semibold text-gray-800"),
                rx.cond(
                    QueryState.current_results["rows"].length() > 0,
                    rx.el.span(
                        f"{QueryState.current_results['rows'].length()} rows",
                        class_name="text-xs text-gray-500",
                    ),
                ),
                class_name="flex items-center justify-between px-4 pt-2",
            ),
            results_table(),
            class_name="flex-1 flex flex-col border-t border-gray-200 bg-white",
        ),
        class_name="flex-1 flex flex-col overflow-hidden",
    )


def editor_panel() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            _tab_button("Query", "query"),
            _tab_button("ER Diagram", "er_diagram"),
            class_name="flex border-b border-gray-200 bg-gray-50",
        ),
        rx.cond(UIState.active_editor_tab == "query", query_view(), er_diagram_view()),
        class_name="flex-1 flex flex-col overflow-hidden",
    )