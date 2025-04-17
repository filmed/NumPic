import customtkinter as ctk
from widgets.custom_panel import CustomPanel


class ContainerPanel(CustomPanel):
    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        CustomPanel.__init__(self, master, _event_bus, **kwargs)
        if _is_last:
            self.init_subscribes()