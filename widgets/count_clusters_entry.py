import customtkinter as ctk
from widgets.base import BaseWidget
from utils.algs import is_child_of
import re


class CountClustersEntry(BaseWidget, ctk.CTkEntry):

    subscriptions = {"focus_changed": "on_focus_changed"}
    binds = {"<Control-v>": "handle_paste"}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkEntry.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.configure(validate="key", validatecommand=(self.register(self.validate_input), "%P"))
        self.is_focused = False
        self.build_view()
        if _is_last:
            self.init_subscribes()

    def build_view(self):
        selection_color = self.additional_styles.get("selection_color", "#C36743")
        selection_text_color = self.additional_styles.get("selection_text_color", "#FFFFFF")
        self._entry.configure(selectbackground=selection_color, selectforeground=selection_text_color)

    def on_focus_changed(self, _focus_object):
        if is_child_of(_focus_object, self):
            if not self.is_focused:
                self.unlock_entry()
        else:
            if self.is_focused:
                self.lock_entry()

    def validate_input(self, new_text: str) -> bool:
        if not self.is_focused and self.master.focus_get() != self:
            return True
        return len(new_text) <= 2 and re.fullmatch(r"[0-9]{0,2}", new_text) is not None

    def lock_entry(self):
        self.is_focused = False
        self.master.focus_set()

    def unlock_entry(self):
        if not self.is_focused:
            self.is_focused = True
            self.configure(state="normal")
            self.focus_set()
            self.icursor("end")

    def handle_paste(self, event):
        if self.is_focused:
            clipboard_text = self.master.clipboard_get()
            filtered = re.sub(r"[^0-9]", "", clipboard_text)[:2]
            self.delete(0, "end")
            self.insert(0, filtered)
        return "break"

    def get_value(self):
        val = self.get()
        return int(val) if val.isdigit() and len(val) <= 2 else None