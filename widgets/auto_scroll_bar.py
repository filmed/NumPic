from widgets.base import BaseWidget
import customtkinter as ctk


class AutoScrollbar(BaseWidget, ctk.CTkScrollbar):
    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkScrollbar.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)
        if _is_last:
            self.init_subscribes()


    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            ctk.CTkScrollbar.set(self, lo, hi)
            self.grid()
