import reflex as rx
from typing import Literal


class UIState(rx.State):
    status_text: str = "Not Connected"
    active_editor_tab: str = "query"
    show_import_modal: bool = False
    show_connect_db_modal: bool = False
    show_new_session_modal: bool = False
    import_source_type: Literal["file", "url"] = "file"
    import_url: str = ""

    @rx.event
    def toggle_import_modal(self):
        self.show_import_modal = not self.show_import_modal

    @rx.event
    def toggle_connect_db_modal(self):
        self.show_connect_db_modal = not self.show_connect_db_modal

    @rx.event
    def toggle_new_session_modal(self):
        self.show_new_session_modal = not self.show_new_session_modal

    @rx.event
    def set_import_source_type(self, type: Literal["file", "url"]):
        self.import_source_type = type

    @rx.event
    def set_import_url(self, url: str):
        self.import_url = url

    @rx.event
    def set_active_editor_tab(self, tab_name: str):
        self.active_editor_tab = tab_name