from widgets.custom_radio_button import CustomRadioButton


class PalletRadioButton(CustomRadioButton):

    def __init__(self, master, _event_bus, _color, _variable, _value, _is_last=False, **kwargs):
        CustomRadioButton.__init__(self, master=master, _event_bus=_event_bus, _variable=_variable, _value=_value, **kwargs)
        self.color = _color
        self.styles_on["color"] = self.color
        self.styles_off["color"] = self.color
        self.image_on = self.build_view(self.styles_on)
        self.image_off = self.build_view(self.styles_off)
        self.update_button()

        if _is_last:
            self.init_subscribes()

    def on_activate(self, **kwargs):
        self.event_bus.send_state("color_modify", self.color)
