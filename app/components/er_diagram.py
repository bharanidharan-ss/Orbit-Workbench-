import reflex as rx
from app.state import QueryState


def er_diagram_view() -> rx.Component:
    return rx.el.div(
        rx.markdown(
            QueryState.er_diagram_markdown, component_map={"erDiagram": rx.el.div}
        ),
        class_name="w-full h-full p-4 overflow-auto bg-white flex items-center justify-center",
    )