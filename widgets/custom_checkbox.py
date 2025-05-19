import os
from widgets.base import BaseWidget
import customtkinter as ctk
from PIL import Image, ImageDraw
import sprites
import copy
from utils.color_models import hex2rgb


class CustomCheckBox(BaseWidget, ctk.CTkLabel):
    binds = {**BaseWidget.binds, "<ButtonPress-1>": "on_click"}

    def __init__(self, master, _event_bus, _is_last=False, command=None, **kwargs):
        ctk.CTkLabel.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.command = command
        self.state = False

        self.styles_on = copy.deepcopy(self.additional_styles.get('styles_on', {'color': '#AAAAAA', 'size': 30}))
        self.styles_off = copy.deepcopy(self.additional_styles.get('styles_off', {'color': '#555555', 'size': 30}))

        self.icon_on = self.build_icon(self.styles_on)
        self.icon_off = self.build_icon(self.styles_off)

        self.image_on = self.build_view(self.styles_on, self.icon_on)
        self.image_off = self.build_view(self.styles_off, self.icon_off)

        self.configure(image=self.image_off)

        if _is_last:
            self.init_subscribes()

    def on_click(self, event=None):
        self.state = not self.state
        self.update_button()
        if self.command:
            self.command(self.state)

    def update_button(self):
        if self.state:
            self.configure(image=self.image_on)
            self.on_activate()
        else:
            self.configure(image=self.image_off)
            self.on_deactivate()

    def on_activate(self, **kwargs):
        pass

    def on_deactivate(self, **kwargs):
        pass

    def get(self):
        return self.state

    def set(self, value: bool):
        self.state = bool(value)
        self.update_button()
        if self.command:
            self.command(self.state)

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
        size = round(_styles['size'])
        self.size = size
        color = _styles.get('color', '#FF000000')
        border_color = _styles.get('border_color', '#FFFFFF')
        inner_border_color = _styles.get('inner_border_color', '#000000')
        border_width = round(_styles.get('border_width', 1))
        inner_border_width = round(_styles.get('inner_border_width', 1))
        corner_radius = round(_styles.get('corner_radius', 5))
        icon_resizable = _styles.get('icon_resizable', True)
        icon_color = _styles.get('icon_color', None)

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

        offset = border_width * 2
        draw.rounded_rectangle(
            (offset, offset, img_size - 1 - offset, img_size - 1 - offset),
            radius=corner_radius * 2,
            outline=inner_border_color,
            width=inner_border_width * 2
        )

        img = img.resize((size, size), Image.Resampling.LANCZOS)

        if _icon:
            if icon_color and _icon.mode in ('RGB', 'RGBA'):
                if _icon.mode != 'RGBA':
                    _icon = _icon.convert('RGBA')
                r, g, b, a = _icon.split()
                mask = a if 'A' in _icon.getbands() else None
                r, g, b = hex2rgb(icon_color)
                color_layer = Image.new('RGBA', _icon.size, (r, g, b, 255))
                _icon = Image.composite(color_layer, _icon, mask or _icon)

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