from widgets.custom_panel import CustomPanel
from widgets.base import BaseWidget
from widgets.layer_miniature import LayerMiniature
import customtkinter as ctk
import copy
from utils.algs import is_child_of
import regex

# additional_styles: {
#   styles_on: {
#       !size
#       color
#       border_color
#       inner_border_color
#       border_width
#       inner_border_width
#       corner_radius
#       icon_resizable
#       icon
#       icon_color
#   }
#  styles_off: {<--->}
# }


class LayerEntry(BaseWidget, ctk.CTkEntry):

    subscriptions = {"focus_changed": "on_focus_changed"}
    binds = {"<Control-v>": "handle_paste", "<KeyRelease>": "format_input"}
    def __init__(self, master, _event_bus, _name, _max_len=20, _is_last=False, **kwargs):
        ctk.CTkEntry.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.max_len = _max_len
        self.name = None
        self.is_focused = False

        self.configure(validate="key", validatecommand=(self.register(self.validate_input), "%P"))

        self.set_name(_name)


        if _is_last:
            self.init_subscribes()


    def on_focus_changed(self, _focus_object):

        if is_child_of(_focus_object, self):
            if not self.is_focused:
                self.unlock_entry()
        else:
            if self.is_focused:
                self.lock_entry()

    def set_name(self, _name):
        filtered_text = regex.sub(r"[^\p{L}\d\s.,!?]", "", _name.strip())[:self.max_len]
        print(filtered_text)
        self.insert(0, filtered_text.upper())
        self.name = filtered_text

    def validate_input(self, new_text: str) -> bool:
        if not self.is_focused and self.master.focus_get() != self:
            return True
        return len(new_text) <= self.max_len and regex.fullmatch(r"^[\s\p{L}\d.,!?]*$", new_text) is not None

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
            filtered_text = regex.sub(r"[^\p{L}\d\s.,!?]", "", clipboard_text)[:self.max_len]
            self.delete(0, "end")
            self.insert(0, filtered_text.upper())
        return "break"

    def format_input(self, event):
        if self.is_focused:
            current_text = self.get()
            if current_text != current_text.upper():
                self.delete(0, "end")
                self.insert(0, current_text.upper())

    def get_name(self) -> str:
        text = self.get().strip()
        return text.upper() if len(text) <= self.max_len else ""


class LayerRadioButton(CustomPanel):

    binds = {**CustomPanel.binds, "<ButtonPress-1>": "on_click"}

    def __init__(self, master, _event_bus, _name, _variable, _img, _is_last=False, **kwargs):
        CustomPanel.__init__(self, master=master,  _event_bus=_event_bus)

        self.variable = _variable
        self.name = _name
        self.img = _img

        self.styles_on = copy.deepcopy(self.additional_styles.get('styles_on', {'color': '#AAAAAA'}))
        self.styles_off = copy.deepcopy(self.additional_styles.get('styles_off', {'color': '#555555'}))

        if self.variable:
            self.trace_id = self.variable.trace_add("write", lambda *args: self.update_button())

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="", padx=(10, 10), pady=(10, 10))

        self.container.grid_columnconfigure(0, weight=0)  # miniature
        self.container.grid_columnconfigure(1, weight=0)  # entry
        self.container.grid_rowconfigure(0, weight=1)

        self.miniature = LayerMiniature(self.container, self.event_bus, self.img, _is_last=True)
        self.miniature.grid(row=0, column=0, padx=(0, 5), pady=(0, 0), sticky="w")

        self.entry = LayerEntry(self.container, self.event_bus, self.name, _is_last=True)
        self.entry.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky="nsew")

        self.miniature.bind("<Button-1>", self.on_click)
        self.container.bind("<Button-1>", self.on_click)
        self.entry.bind("<Button-1>", self.on_click)

        if _is_last:
            self.init_subscribes()

    def destroy(self):
        if hasattr(self, "trace_id") and self.variable:
            self.variable.trace_remove("write", self.trace_id)
        super().destroy()

    def on_click(self, event=None):
        if self.variable:
            self.variable.set(self.name)

    def update_button(self):
        if self.variable and self.variable.get() == self.name:
            self.build_view(self.styles_on)
            self.on_activate()
        else:
            self.build_view(self.styles_off)
            self.on_deactivate()

    def on_activate(self, **kwargs):
        self.event_bus.send_state("layer_select", self.name)

    def on_deactivate(self, **kwargs):
        pass

    def build_view(self,  _styles):
        color = _styles.get("color", "#AAAAAA")
        width = _styles.get("width", 65)
        text_color = _styles.get("text_color", "#000000")
        entry_color = _styles.get("entry_color", "#AAAAAA")
        miniature_indent = _styles.get("miniature_indent", 5)

        selection_color = _styles.get("selection_color", "#C36743")
        selection_text_color = _styles.get("selection_text_color", "#FFFFFF")

        entry_border_width = _styles.get("entry_border_width", 0)
        container_border_width = _styles.get("container_border_width", 0)
        entry_padx = _styles.get("entry_padx", (0, 0))
        entry_pady = _styles.get("entry_pady", (0, 0))
        container_padx = _styles.get("container_padx", (0, 0))
        container_pady = _styles.get("container_pady", (0, 0))

        self.configure(fg_color=color)
        self.entry.configure(text_color=text_color, border_color=text_color, fg_color=entry_color)
        self.container.configure(border_color=text_color)

        self.entry.configure(border_width=entry_border_width, width=width)
        self.container.configure(border_width=container_border_width)
        self.entry._entry.configure(selectbackground=selection_color, selectforeground=selection_text_color)

        self.miniature.grid_configure(padx=(entry_padx[0], miniature_indent), pady=entry_pady)
        self.entry.grid_configure(padx=(0, entry_padx[1]), pady=entry_pady)
        self.container.grid_configure(padx=container_padx, pady=container_pady)

