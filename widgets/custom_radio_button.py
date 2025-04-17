import os
from widgets.base import BaseWidget
import customtkinter as ctk
from PIL import Image, ImageDraw
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
#       icon
#   }
#  styles_off: {<--->}
# }


class CustomRadioButton(BaseWidget, ctk.CTkLabel):

    binds = {**BaseWidget.binds, "<ButtonPress-1>": "on_click"}

    def __init__(self, master, _event_bus, _variable, _value, _is_last=False, **kwargs):
        ctk.CTkLabel.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.variable = _variable
        self.value = _value
        self.size = None
        self.styles_on = self.additional_styles.get('styles_on', {'color': '#AAAAAA', 'size': 30})
        self.styles_off = self.additional_styles.get('styles_off', {'color': '#555555', 'size': 30})

        self.icon_on = self.build_icon(self.styles_on)
        self.icon_off = self.build_icon(self.styles_off)

        self.image_on = self.build_view(self.styles_on, self.icon_on)
        self.image_off = self.build_view(self.styles_off, self.icon_off)

        self.configure(image=self.image_off)

        if self.variable:
            self.variable.trace_add("write", lambda *args: self.update_button())

        if _is_last:
            self.init_subscribes()

    def on_click(self, event=None):
        if self.variable:
            self.variable.set(self.value)

    def update_button(self):
        if self.variable and self.variable.get() == self.value:
            self.configure(image=self.image_on)
            self.on_activate()
        else:
            self.configure(image=self.image_off)
            self.on_deactivate()

    def on_activate(self, **kwargs):
        pass

    def on_deactivate(self, **kwargs):
        pass

    def build_icon(self, _styles, **kwargs):
        icon = None
        icon_path = _styles.get('icon', None)
        if icon_path:
            sprites_dir = os.path.dirname(sprites.__file__)
            full_path = os.path.join(sprites_dir, os.path.basename(icon_path))
            icon = Image.open(full_path)
            if icon.mode != 'RGBA':
                icon = icon.convert('RGBA')
        return icon

    def build_view(self, _styles, _icon=None):
        size = _styles['size']
        self.size = size
        color = _styles.get('color', '#FF000000')
        border_color = _styles.get('border_color', '#FFFFFF')
        inner_border_color = _styles.get('inner_border_color', '#000000')
        border_width = _styles.get('border_width', 1)
        inner_border_width = _styles.get('inner_border_width', 1)
        corner_radius = _styles.get('corner_radius', 5)
        icon_resizable = _styles.get('icon_resizable', True)

        img_size = 2 * size
        img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle(
            (0, 0, img_size - 1, img_size - 1),
            radius=corner_radius * 2,
            outline=border_color,
            width=border_width * 2,
            fill=color
        )

        # Внутренний бордер
        offset = border_width * 2
        draw.rounded_rectangle(
            (offset, offset, img_size - 1 - offset, img_size - 1 - offset),
            radius=corner_radius * 2,
            outline=inner_border_color,
            width=inner_border_width * 2
        )

        img = img.resize((size, size), Image.Resampling.LANCZOS)

        if _icon:
            icon_w, icon_h = _icon.size
            max_icon_size = size - 2 * (border_width + inner_border_width)

            if icon_resizable:
                _icon.thumbnail((max_icon_size, max_icon_size), Image.Resampling.LANCZOS)
                icon_w, icon_h = _icon.size
            else:
                if icon_w > max_icon_size or icon_h > max_icon_size:
                    _icon.thumbnail((max_icon_size, max_icon_size), Image.Resampling.LANCZOS)
                    icon_w, icon_h = _icon.size

            position = ((size - icon_w) // 2, (size - icon_h) // 2)

            if _icon.mode == 'RGBA':
                img.paste(_icon, position, mask=_icon)
            else:
                img.paste(_icon, position)

        return ctk.CTkImage(img, size=(size, size))

