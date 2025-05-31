from widgets.pallet_radio_button import PalletRadioButton
from widgets.custom_radio_button_frame import CustomRadioButtonFrame


class PalletRadioButtonFrame(CustomRadioButtonFrame):
    subscriptions = {"color_added": "add_color", "color_deleted" : "remove"}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        CustomRadioButtonFrame.__init__(self, master=master, _event_bus=_event_bus, **kwargs)
        if _is_last:
            self.init_subscribes()

    def add_color(self, _color):
        if not _color:
            return
        if _color not in self.buttons:

            button = PalletRadioButton(self, self.event_bus, _color, self.variable, _color, _is_last=True)
            self.buttons[_color] = button

            if not self.object_full_size:
                self.init_object_full_size(button)

            self.columns = self.calc_columns()
            self.rows = self.calc_rows()
            self.buttons[_color].grid(row=self.rows - 1, column=(len(self.buttons) - 1) % self.columns, padx=self.object_padx, pady=self.object_pady, sticky="nw")

            self.update_scrollbar()

