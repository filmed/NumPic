import customtkinter as ctk
from widgets.base import BaseWidget
from widgets.layer_radio_button import LayerRadioButton
from core.models.layer import Layer


class LayerButtonFrame(BaseWidget, ctk.CTkScrollableFrame):

    subscriptions = {"layer_added": "add", "layer_deleted": "delete", "layer_moved": "move", "layer_deleted_all": "delete_all", "layer_rendered": "layer_rendered"}
    binds = {**BaseWidget.binds}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkScrollableFrame.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.root = master
        self.buttons: list[LayerRadioButton] = []
        self.variable = ctk.StringVar(value="")
        self.rows = None
        self.grid_columnconfigure(0, weight=1)

        self.object_full_height = None
        self.object_padx, self.object_pady = None, None

        self.is_scrollable = True
        self._scrollbar.grid_remove()

        if _is_last:
            self.init_subscribes()

    # -----------------------------------logic----------------------------------------------
    def add(self, _data: Layer):
        if _data is None:
            return
        _name, _img = _data.name, _data.img
        _index = len(self.buttons)
        button = LayerRadioButton(self, self.event_bus, _name, self.variable, _img, _is_last=True)
        self.buttons.append(button)
        self.buttons[-1].on_click()

        if not self.object_full_height:
            self.init_object_full_height(button)

        self.rows = _index + 1
        self.buttons[_index].grid(row=self.rows - 1, column=0, padx=self.object_padx, pady=self.object_pady, sticky="nwe")
        self.update_scrollbar()

    def delete(self, _data):
        if _data is None:
            return
        _index, _new_index = _data
        if 0 <= _index < len(self.buttons):
            self.buttons[_index].grid_forget()
            self.buttons[_index].destroy()
            self.buttons.pop(_index)
        if not (_new_index is None) and  0 <= _new_index < len(self.buttons):
            self.buttons[_new_index].on_click()
        self.update_frame()


    def move(self, _data):
        if _data is None:
            return
        _index, _new_index = _data
        if 0 <= _index < len(self.buttons):
            self.buttons[_index], self.buttons[_new_index] = self.buttons[_new_index], self.buttons[_index]
            self.buttons[_new_index].on_click()
            self.update_frame()


    def delete_all(self, _data):
        if _data is None:
            return
        if not self.buttons:
            return

        for btn in self.buttons:
            btn.grid_forget()
            btn.destroy()

        self.buttons.clear()
        self.rows = 0
        self.update_scrollbar()


    def layer_rendered(self, _index):
        if _index is None:
            return
        if 0 <= _index < len(self.buttons):
            print(F"UPDATED IMG AT INDEX{_index}")
            self.buttons[_index].miniature.update_img()


     # -----------------------------------render----------------------------------------------
    def init_object_full_height(self, _object: LayerRadioButton):
        if not (self.object_padx and self.object_pady):
            self.object_padx = tuple(self.additional_styles.get("padx", (1, 1)))
            self.object_pady = tuple(self.additional_styles.get("pady", (1, 1)))
        height = int(_object.cget("height"))
        self.object_full_height = self.object_pady[0] + height + self.object_pady[1]

    def update_frame(self, event=None):
        if not self.object_full_height:
            return

        for i in range(len(self.buttons)):
            self.buttons[i].grid(row=i, column=0, padx=self.object_padx, pady=self.object_pady, sticky="we")

        self.update_scrollbar()

    def update_scrollbar(self):
        rows = len(self.buttons)
        total_height = rows * self.object_full_height
        info = self.grid_info()
        row, rowspan, column, columnspan = info["row"], info["rowspan"], info["column"], info["columnspan"]
        bbox = self.root.grid_bbox(column, row, column + columnspan - 1, row + rowspan - 1)
        visible_height = bbox[3]

        if total_height > visible_height and not self.is_scrollable:
            self._scrollbar.grid()
            self.is_scrollable = True
        elif total_height <= visible_height and self.is_scrollable:
            self.is_scrollable = False
            self._scrollbar.grid_remove()



