import customtkinter as ctk
from widgets.base import BaseWidget
from widgets.custom_radio_button import CustomRadioButton


class CustomRadioButtonFrame(BaseWidget, ctk.CTkScrollableFrame):

    binds = {**BaseWidget.binds, '<Configure>': 'update_frame'}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkScrollableFrame.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.root = master
        self.buttons = {}
        self.variable = ctk.StringVar(value="")
        self.rows = None
        self.columns = None

        self.object_full_size = None
        self.object_padx, self.object_pady = None, None

        self.is_scrollable = True
        self._scrollbar.grid()

        if _is_last:
            self.init_subscribes()

    # -----------------------------------logic----------------------------------------------
    def add(self, **kwargs):
        pass

    def remove(self, _key):
        if _key in self.buttons:
            self.buttons[_key].destroy()
            del self.buttons[_key]
            self.update_frame()


            # -----------------------------------render----------------------------------------------
    def init_object_full_size(self, _object: CustomRadioButton):
        if not (self.object_padx and self.object_pady):
            self.object_padx = tuple(self.additional_styles.get("padx", (1, 1)))
            self.object_pady = tuple(self.additional_styles.get("pady", (1, 1)))
        size = round(_object.size)
        self.object_full_size = (self.object_padx[0] + size + self.object_padx[1], self.object_pady[0] + size + self.object_pady[1])

    def calc_columns(self):
        self.update()
        width = self.winfo_width() if self.winfo_width() > 1 else int(self.cget("width"))
        return max(1, width // self.object_full_size[0])

    def calc_rows(self):
        count = len(self.buttons)
        return (count + self.columns - 1) // self.columns

    def update_frame(self, event=None):
        if not self.object_full_size:
            return
        new_columns = self.calc_columns()
        new_rows = self.calc_rows()

        if new_columns != self.columns or new_rows != self.rows:
            if new_columns != self.columns:
                self.columns = new_columns
                self.grid_columnconfigure(list(range(self.columns)), weight=0)

            for i, key in enumerate(self.buttons):
                self.buttons[key].grid(row=i // self.columns, column=i % self.columns, padx=self.object_padx, pady=self.object_pady, sticky="nw")

            if new_rows != self.rows:
                self.rows = new_rows

        self.update_scrollbar()

    def update_scrollbar(self):
        rows = self.calc_rows()
        total_height = rows * self.object_full_size[1]
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



