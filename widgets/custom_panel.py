from widgets.base import BaseWidget
import customtkinter as ctk


class CustomPanel(BaseWidget, ctk.CTkFrame):

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkFrame.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)
        if _is_last:
            self.init_subscribes()
