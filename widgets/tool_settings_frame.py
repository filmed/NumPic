import customtkinter as ctk
from widgets.custom_panel import CustomPanel
from widgets.custom_slider import CustomSlider
from widgets.custom_checkbox import CustomCheckBox
from widgets.container_panel import ContainerPanel


class ToolSettingsFrame(CustomPanel):
    subscriptions = {"tool_settings_changed": "load_settings_from_tool"}
    binds = {**CustomPanel.binds}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        CustomPanel.__init__(self, master, _event_bus, **kwargs)
        self.event_bus = _event_bus
        self.widgets = {}

        self.container = ctk.CTkFrame(self, fg_color="transparent", border_width=0, height=int(self.cget("height")))
        self.container.grid(row=0, column=0, sticky="", padx=(5, 5), pady=(0, 0))
        self.container.grid_rowconfigure(0, weight=1)

        if _is_last:
            self.init_subscribes()

        self.columnconfigure("all", weight=1)

    def clear(self):
        for widget in self.widgets.values():
            widget.destroy()
        self.widgets.clear()

    def load_settings_from_tool(self, _tool):
        if _tool is None:
            return

        self.clear()
        schema = getattr(_tool, "settings", {})
        column = 0

        for key, info in schema.items():
            if info["type"] == "slider":
                slider = CustomSlider(
                    master=self.container,
                    _event_bus=self.event_bus,
                    from_=info.get("min", 0),
                    to=info.get("max", 100),
                    step=info.get("step", 1),
                    command=lambda value, k=key: self.update_tool_setting(_tool, k, value),
                    _is_last=True
                )
                slider.set(getattr(_tool, key, info.get("default", 0)))
                slider.grid(row=0, column=column, padx=10, pady=5, sticky="nsew")
                self.widgets[key] = slider

            elif info["type"] == "checkbox":
                checkbox = CustomCheckBox(
                    master=self.container,
                    _event_bus=self.event_bus,
                    command=lambda value, k=key: self.update_tool_setting(_tool, k, value),
                    _is_last=True
                )
                checkbox.set(getattr(_tool, key, info.get("default", False)))
                checkbox.grid(row=0, column=column, padx=10, pady=5, sticky="nsew")
                self.widgets[key] = checkbox

            self.container.grid_columnconfigure(column, weight=0)
            column += 1

    def update_tool_setting(self, tool, key, value):
        setattr(tool, key, value)
