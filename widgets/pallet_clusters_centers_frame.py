import customtkinter as ctk
from widgets.base import BaseWidget
from widgets.pallet_radio_button import PalletRadioButton
from widgets.custom_radio_button_frame import CustomRadioButtonFrame
from widgets.pallet_cluster_center_radio_button import PalletClusterCenterRadioButton


class PalletClustersCentersFrame(CustomRadioButtonFrame):
    subscriptions = {"center_add": "add_center", "center_delete" : "remove", "centers_delete_all": "delete_all", "center_color_change": "color_change"}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        CustomRadioButtonFrame.__init__(self, master=master, _event_bus=_event_bus, **kwargs)
        if _is_last:
            self.init_subscribes()

    def add_center(self, _center_color):
        print(f'add_center: {_center_color}')
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


    def delete_all(self, _data):
        if _data is None:
            return
        if not self.buttons:
            return

        for _key in self.buttons:
            self.buttons[_key].grid_forget()
            self.buttons[_key].destroy()
        self.buttons.clear()


    def color_change(self, _data):
        if _data is None:
            return

        _old_color, _new_color = _data

        if _old_color in self.buttons and _new_color not in self.buttons:
            btn = self.buttons.pop(_old_color)
            btn.color_change(_new_color)
            self.buttons[_new_color] = btn

            self.event_bus.send_state("center_color_changed")

