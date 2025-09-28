import reflex as rx
from app.states.query_state import QueryState


def results_table() -> rx.Component:
    return rx.el.div(
        rx.cond(
            QueryState.current_results["rows"].length() > 0,
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.foreach(
                                QueryState.current_results["columns"],
                                lambda col: rx.el.th(
                                    col,
                                    class_name="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50",
                                ),
                            ),
                            class_name="border-b border-gray-200",
                        )
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            QueryState.current_results["rows"],
                            lambda row: rx.el.tr(
                                rx.foreach(
                                    row,
                                    lambda item: rx.el.td(
                                        item.to_string(),
                                        class_name="px-4 py-2 text-sm text-gray-700 whitespace-nowrap",
                                    ),
                                ),
                                class_name="border-b border-gray-200 hover:bg-gray-50",
                            ),
                        )
                    ),
                    class_name="w-full",
                ),
                class_name="w-full overflow-auto border border-gray-200 rounded-lg",
            ),
            rx.el.div(
                rx.icon("circle_play", size=32, class_name="text-gray-400 mb-2"),
                rx.el.p(
                    "Run a query to see results.", class_name="text-sm text-gray-500"
                ),
                class_name="flex flex-col items-center justify-center h-full text-center p-8 bg-gray-50 rounded-lg",
            ),
        ),
        class_name="flex-1 w-full p-4 overflow-auto",
    )