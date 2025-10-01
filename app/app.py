import reflex as rx
from app.components.header import header
from app.components.sidebar import sidebar
from app.components.editor import editor_panel
from app.components.status_bar import status_bar
from app.components.modals import (
    import_modal,
    connect_db_modal,
    new_session_modal,
    import_session_modal,
)
from app.state import DBState


def index() -> rx.Component:
    """The main page of the application."""
    return rx.el.main(
        rx.el.div(
            header(),
            rx.el.div(
                sidebar(), editor_panel(), class_name="flex flex-1 overflow-hidden"
            ),
            status_bar(),
            import_modal(),
            connect_db_modal(),
            new_session_modal(),
            import_session_modal(),
            class_name="flex flex-col h-full",
        ),
        class_name="font-['Poppins'] h-screen bg-white",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, route="/", title="Orbit Workbench", on_load=DBState.initialize_db)