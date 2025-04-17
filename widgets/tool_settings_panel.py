# from widgets.container_panel import ContainerPanel
# import customtkinter as ctk
#
#
# class ToolSettingsPanel(ContainerPanel):
#     subscriptions = {"tool_changed": "change_settings"}
#
#     def __init__(self, master, _event_bus, _is_last=False, **kwargs):
#         ContainerPanel.__init__(self, master, _event_bus, **kwargs)
#         self.tools_settings = {}
#         if _is_last:
#             self.init_subscribes()
#
#     def change_settings(self, _tool_name):
#         if not _tool_name:
#             return
#         if _tool_name in self.tools_settings:
#
#
#
#     def add_tool_settings(self, _tool_name, ):
#         self.tools_settings[_tool_name] = []
#