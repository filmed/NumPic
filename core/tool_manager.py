# Provides tool logic: defines when and which tool should be active, adjusts bindings
from utils.algs import unbind

class ToolManager:
    def __init__(self, _event_bus):
        self.event_bus = _event_bus
        self.tools = {}
        self.use_zones = {}
        self.tool_settings = {}
        self.current_tool = None
        self.cursor_binds = {}

        self.event_bus.subscribe("tool_changed", self.on_tool_changed)

    def add_tool(self, _name, _tool):
        self.tools[_name] = _tool

    def add_use_zone(self, _name, _use_zone):
        self.use_zones[_name] = _use_zone

    def on_tool_changed(self, _tool_name):
        if self.current_tool:
            self.unbind_tool(self.current_tool)
            self.current_tool.deactivate()
        if _tool_name in self.tools:
            self.current_tool = self.tools[_tool_name]
            self.current_tool.activate()
            self.bind_tool(self.current_tool)



            self.event_bus.send_state("tool_settings_changed", self.current_tool)

    def bind_tool(self, _tool):
        for zone in _tool.use_zones:
            self.use_zones[zone].canvas.configure(cursor="none")

            for event, func in _tool.get_binds().items():
                bind_id = self.use_zones[zone].canvas.bind(event, func,  add="+")
                _tool.binds_ids[(zone, event)] = bind_id

            motion_id = self.use_zones[zone].canvas.bind( "<Motion>", _tool.update_cursor_view, add="+")
            wheel_id = self.use_zones[zone].canvas.bind( "<MouseWheel>", _tool.update_cursor_view, add="+")
            drag_id = self.use_zones[zone].canvas.bind( "<B1-Motion>", _tool.update_cursor_view, add="+")

            self.cursor_binds[(zone,"<Motion>")] = motion_id
            self.cursor_binds[(zone,"<MouseWheel>")] = wheel_id
            self.cursor_binds[(zone,"<B1-Motion>")] = drag_id


    def unbind_tool(self, _tool):
        for (zone, event), bind_id in _tool.binds_ids.items():
            try:
                unbind(self.use_zones[zone].canvas, event, bind_id)

            except Exception as e:
                print(f"[unbind_tool] Error unbinding {event} from {zone}: {e}")

        _tool.binds_ids.clear()

        # cursor unbinding
        for (zone, event), bind_id in self.cursor_binds.items():
            try:
                unbind(self.use_zones[zone].canvas, event, bind_id)
            except Exception as e:
                print(f"[unbind_tool] Error unbinding {event} from {zone}: {e}")

        self.cursor_binds.clear()

        for zone in _tool.use_zones:
            self.use_zones[zone].canvas.configure(cursor="arrow")


