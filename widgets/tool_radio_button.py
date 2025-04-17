import os
from PIL import Image
from widgets.custom_radio_button import CustomRadioButton
import sprites

# additional_styles: {
#   styles_on: {
#       !size
#       color
#       border_color
#       inner_border_color
#       border_width
#       inner_border_width
#       corner_radius
#       icon_resizable
#       icons: {
#           "tool_name1" : "icon_1.png",
#           "tool_name2" : "icon_2.png",
#           "tool_name3" : "icon_3.png",
#                       .........
#       }
#   }
#  styles_off: {<--->}
# }

class ToolRadioButton(CustomRadioButton):
    def __init__(self, master, _event_bus, _tool_name, _variable, _value, _is_last=False, **kwargs):
        self.tool_name = _tool_name
        CustomRadioButton.__init__(self, master=master, _event_bus=_event_bus, _variable=_variable, _value=_value, **kwargs)
        if _is_last:
            self.init_subscribes()

    def build_icon(self, _styles, **kwargs):
        icon = None
        icon_path = None
        icons_styles = _styles.get('icons', None)
        if icons_styles:
            icon_path = icons_styles.get(self.tool_name, None)
        if icon_path:
            sprites_dir = os.path.dirname(sprites.__file__)
            full_path = os.path.join(sprites_dir, os.path.basename(icon_path))
            icon = Image.open(full_path)
            if icon.mode != 'RGBA':
                icon = icon.convert('RGBA')
        return icon

    def on_activate(self, **kwargs):
        self.event_bus.send_state("tool_changed", self.tool_name)
