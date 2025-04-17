from widgets.custom_button import CustomButton


class PalletAddButton(CustomButton):

    subscriptions = {"color_changed": "update_color"}

    def __init__(self, master, _event_bus, _value=None, _is_last=False, **kwargs):
        CustomButton.__init__(self, master, _event_bus, _value, **kwargs)
        self.color = None
        if _is_last:
            self.init_subscribes()

    def update_color(self, _color):
        if not _color:
            return
        self.color = _color

    def on_activate(self, **kwargs):
        self.event_bus.send_state("color_added", self.color)

