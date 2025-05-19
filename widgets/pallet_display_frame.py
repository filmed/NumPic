from widgets.base import BaseWidget
import customtkinter as ctk
from utils.color_models import hex2rgb
from utils.algs import is_child_of

import re


class HexEntry(BaseWidget, ctk.CTkEntry):

    subscriptions = {"focus_changed": "on_focus_changed"}
    binds = {"<Control-v>": "handle_paste", "<KeyRelease>": "format_input"}
    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkEntry.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.configure(validate="key", validatecommand=(self.register(self.validate_input), "%P"))

        self.is_focused = False

        if _is_last:
            self.init_subscribes()


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
        return len(new_text) <= 6 and re.fullmatch(r"^[0-9A-Fa-f]*$", new_text) is not None

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
            filtered_text = re.sub(r"[^0-9A-Fa-f]", "", clipboard_text)[:6]
            self.delete(0, "end")
            self.insert(0, filtered_text.upper())
        return "break"

    def format_input(self, event):
        if self.is_focused:
            current_text = self.get()
            if current_text != current_text.upper():
                self.delete(0, "end")
                self.insert(0, current_text.upper())

    def get_hex(self) -> str:
        text = self.get().strip()
        return text.upper() if len(text) == 6 else ""

class PalletDisplayFrame(BaseWidget, ctk.CTkFrame):
    subscriptions = {"color_changed": "update_color"}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkFrame.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.color = None
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="", padx=(10, 10), pady=(10, 10))

        self.container.grid_columnconfigure(0, weight=0)  # #
        self.container.grid_columnconfigure(1, weight=0)  # entry
        self.container.grid_rowconfigure(0, weight=1)

        self.hash_label = ctk.CTkLabel(self.container, text="#")
        self.hash_label.grid(row=0, column=0, padx=(0, 5), sticky="e")

        self.entry = HexEntry(self.container, self.event_bus, _is_last=True, width=70, fg_color="transparent")
        self.entry.grid(row=0, column=1, sticky="w")

        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<KeyRelease>", self.on_enter, add="+")

        self.build_view()

        if _is_last:
            self.init_subscribes()

    def build_view(self):
        width = self.additional_styles.get("width", 65)
        hash_indent = self.additional_styles.get("hash_indent", 5)

        selection_color = self.additional_styles.get("selection_color", "#C36743")
        selection_text_color = self.additional_styles.get("selection_text_color", "#FFFFFF")

        entry_border_width = self.additional_styles.get("entry_border_width", 0)
        container_border_width = self.additional_styles.get("container_border_width", 0)
        entry_padx = self.additional_styles.get("entry_padx", (0, 0))
        entry_pady = self.additional_styles.get("entry_pady", (0, 0))
        container_padx = self.additional_styles.get("container_padx", (0, 0))
        container_pady = self.additional_styles.get("container_pady", (0, 0))


        self.entry.configure(width=width,border_width=entry_border_width)
        self.container.configure(border_width=container_border_width)
        self.entry._entry.configure(selectbackground=selection_color, selectforeground=selection_text_color)

        self.hash_label.grid_configure(padx=(entry_padx[0], hash_indent), pady=entry_pady)
        self.entry.grid_configure(padx=(0, entry_padx[1]), pady=entry_pady)
        self.container.grid_configure(padx=container_padx, pady=container_pady)


    def update_color(self, _color):
        if not _color:
            return
        hex_val = _color.lstrip("#").upper()
        self.entry.delete(0, "end")
        self.entry.insert(0, hex_val)
        self.set_color(f"#{hex_val}")

    def on_enter(self, event=None):
        color = self.entry.get_hex()
        if color:
            self.event_bus.send_state("color_modify", f'#{color}')

    def _is_valid_hex(self, s):
        return re.fullmatch(r"[0-9a-fA-F]{6}", s) is not None

    def set_color(self, _color):
        if _color:
            self.color = _color
            self.configure(fg_color=self.color)
            text_color = self.calc_text_color(self.color)
            self.hash_label.configure(text_color=text_color)
            self.entry.configure(text_color=text_color, border_color=text_color)
            self.container.configure(border_color=text_color)

    def calc_text_color(self, color):
        rgb = hex2rgb(color)
        L = round(rgb[0] * 299 / 1000 + rgb[1] * 587 / 1000 + rgb[2] * 114 / 1000)
        return "#000000" if L > 128 else "#FFFFFF"