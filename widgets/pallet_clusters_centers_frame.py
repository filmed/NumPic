import customtkinter as ctk
from widgets.base import BaseWidget
from widgets.pallet_radio_button import PalletRadioButton
from widgets.custom_radio_button_frame import CustomRadioButtonFrame
from widgets.pallet_cluster_center_radio_button import PalletClusterCenterRadioButton


class PalletClustersCentersFrame(CustomRadioButtonFrame):
    subscriptions = {"center_added": "add_center", "center_deleted" : "remove"}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        CustomRadioButtonFrame.__init__(self, master=master, _event_bus=_event_bus, **kwargs)
        if _is_last:
            self.init_subscribes()

    def add_center(self, _center_color):
        if not _center_color:
            return
        if _center_color not in self.buttons:
            button = PalletClusterCenterRadioButton(self, self.event_bus, _center_color, self.variable, _center_color, _is_last=True)
            self.buttons[_center_color] = button

            if not self.object_full_size:
                self.init_object_full_size(button)

            self.columns = self.calc_columns()
            self.rows = self.calc_rows()
            self.buttons[_center_color].grid(row=self.rows - 1, column=(len(self.buttons) - 1) % self.columns, padx=self.object_padx, pady=self.object_pady, sticky="nw")
            self.update_scrollbar()


    def get_centers(self) -> list[str]:
        return list(self.buttons.keys())
