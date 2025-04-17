from widgets.tool_radio_button import ToolRadioButton
from widgets.custom_radio_button_frame import CustomRadioButtonFrame


class ToolRadioButtonFrame(CustomRadioButtonFrame):

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        CustomRadioButtonFrame.__init__(self, master=master, _event_bus=_event_bus, **kwargs)
        if _is_last:
            self.init_subscribes()

    def add_tool(self, _tool_name):
        if _tool_name not in self.buttons:
            button = ToolRadioButton(self, self.event_bus, _tool_name, self.variable, _tool_name, _is_last=True)
            self.buttons[_tool_name] = button

            if not self.object_full_size:
                self.init_object_full_size(button)

            self.columns = self.calc_columns()
            self.rows = self.calc_rows()
            self.buttons[_tool_name].grid(row=self.rows - 1, column=(len(self.buttons) - 1) % self.columns, padx=self.object_padx, pady=self.object_pady, sticky="nw")
            self.update_scrollbar()

