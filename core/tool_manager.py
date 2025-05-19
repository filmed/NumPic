# Provides tool logic: defines when and which tool should be active, adjusts bindings


class ToolManager:
    def __init__(self, _event_bus):
        self.event_bus = _event_bus
        self.tools = {}
        self.use_zones = {}
        self.tool_settings = {}
        self.current_tool = None

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
            for event, func in _tool.get_binds().items():
                bind_id = self.use_zones[zone].canvas.bind(event, func,  add="+")
                _tool.binds_ids[(zone, event)] = bind_id

    def unbind_tool(self, _tool):
        for (zone, event), bind_id in _tool.binds_ids.items():
            try:
                self.use_zones[zone].canvas.unbind(event, bind_id)
            except Exception as e:
                print(f"[unbind_tool] Error unbinding {event} from {zone}: {e}")
        _tool.binds_ids.clear()

        # for zone in _tool.use_zones:
        #     for (_zone, event), id in _tool.binds_ids.items():
        #         print(f'{(_zone, event)}: {id}')
        #         self.use_zones[zone].canvas.unbind(event, id)

