from widgets.custom_radio_button import CustomRadioButton

class PalletClusterCenterRadioButton(CustomRadioButton):

    binds = {**CustomRadioButton.binds, "<ButtonRelease-3>": "on_delete"}
    subscriptions = {"focus_changed": "on_focus"}

    def __init__(self, master, _event_bus, _color, _variable, _value, _is_last=False, **kwargs):
        CustomRadioButton.__init__(self, master=master, _event_bus=_event_bus, _variable=_variable, _value=_value, **kwargs)
        self.color = _color
        self.styles_on["color"] = self.color
        self.styles_off["color"] = self.color
        self.image_on = self.build_view(self.styles_on)
        self.image_off = self.build_view(self.styles_off)
        self.is_active = False
        self.current_focus = None
        self.setup = None

        if _is_last:
            self.init_subscribes()
        self.update_button()

    def on_activate(self, **kwargs):
        if not self.is_active:
            self.is_active = True
            self.setup = True
            self.event_bus.subscribe("color_changed", self.ask_color_change)

        self.styles_on["color"] = self.color
        self.styles_off["color"] = self.color
        self.image_on = self.build_view(self.styles_on)
        self.image_off = self.build_view(self.styles_off)
        self.configure(image=self.image_on)


    def destroy(self):
        if hasattr(self, "trace_id") and self.variable:
            self.variable.trace_remove("write", self.trace_id)

        self.event_bus.unsubscribe("color_changed", self.ask_color_change)
        self.event_bus.unsubscribe("focus_changed", self.on_focus)
        super().destroy()

    def on_deactivate(self, **kwargs):
        if self.is_active:
            self.is_active = False
            self.setup = False
            self.event_bus.unsubscribe("color_changed", self.ask_color_change)


    def ask_color_change(self, _color):
        if not _color:
            return
        if self.setup:
            self.setup = False
            return
        self.event_bus.send_state("center_color_change", (self.color, _color))

    def color_change(self, _color):
        if not _color:
            return
        if self.setup:
            self.setup = False
            return
        self.color = _color
        self.styles_on["color"] = self.color
        self.styles_off["color"] = self.color
        self.image_on = self.build_view(self.styles_on)
        self.image_off = self.build_view(self.styles_off)
        self.update_button()

    def on_focus(self, _focused_widget):
        if _focused_widget:
            self.current_focus = _focused_widget


    def on_delete(self, event=None):
        self.event_bus.send_state("center_delete", self.color)


