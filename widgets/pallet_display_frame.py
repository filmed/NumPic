from widgets.base import BaseWidget
import customtkinter as ctk
from utils.color_models import hex2rgb


class PalletDisplayFrame(BaseWidget, ctk.CTkLabel):

    subscriptions = {"color_changed": "update_color"}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkLabel.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)
        if _is_last:
            self.init_subscribes()

    def update_color(self, _color):
        if not _color:
            return
        self.configure(text=_color, fg_color=_color, text_color=self.calc_text_color(_color))

    def calc_text_color(self, color):
        rgb = hex2rgb(color)
        L = round(rgb[0] * 299 / 1000 + rgb[1] * 587 / 1000 + rgb[2] * 114 / 1000)
        return "#000000" if L > 128 else "#FFFFFF"
