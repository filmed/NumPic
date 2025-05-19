import os
from widgets.base import BaseWidget
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
import sprites
import fonts
from utils.color_models import hex2rgb

# additional_styles: {
#   styles_idle: {
#       !width
#       !height
#       color
#       border_color
#       inner_border_color
#       border_width
#       inner_border_width
#       corner_radius
#       icon_resizable
#       text
#       text_color
#       font_size
#       font
#       icon
#       icon_color
#   }
#  styles_click: {<--->}
#  styles_hover: {<--->}
# }


class CustomButton(BaseWidget, ctk.CTkLabel):

    binds = {**BaseWidget.binds, "<ButtonPress-1>": "on_click", "<ButtonRelease-1>": "on_release", "<Enter>": "on_hover", "<Leave>": "on_leave"}

    def __init__(self, master, _event_bus, _value=None, _is_last=False, **kwargs):
        ctk.CTkLabel.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.value = _value
        self.size = None
        self.styles_idle = self.additional_styles.get('styles_idle', {'color': '#AAAAAA', 'size': 30})
        self.styles_click = self.additional_styles.get('styles_click', {'color': '#111111', 'size': 30})
        self.styles_hover = self.additional_styles.get('styles_hover', {'color': '#555555', 'size': 30})

        self.icon_idle = self.build_icon(self.styles_idle)
        self.icon_click = self.build_icon(self.styles_click)
        self.icon_hover = self.build_icon(self.styles_hover)

        self.image_idle = self.build_view(self.styles_idle, self.icon_idle)
        self.image_click = self.build_view(self.styles_click, self.icon_click)
        self.image_hover = self.build_view(self.styles_hover, self.icon_hover)

        self.configure(image=self.image_idle)

        if _is_last:
            self.init_subscribes()

    def on_click(self, event=None):
        self.configure(image=self.image_click)

    def on_release(self, event=None):
        self.on_activate()

    def on_hover(self, event=None):
        self.configure(image=self.image_hover)

    def on_leave(self, event=None):
        self.configure(image=self.image_idle)

    def on_activate(self, **kwargs):
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
        width = _styles['width']
        height = _styles['height']
        self.size = (width, height)
        color = _styles.get('color', '#FF000000')
        border_color = _styles.get('border_color', '#FFFFFF')
        inner_border_color = _styles.get('inner_border_color', '#000000')
        border_width = _styles.get('border_width', 0)
        inner_border_width = _styles.get('inner_border_width', 0)
        corner_radius = _styles.get('corner_radius', 5)
        icon_resizable = _styles.get('icon_resizable', True)
        icon_color = _styles.get('icon_color', None)

        text = _styles.get('text', '')
        if self.value:
            text = self.value
        elif text:
            self.value = text

        text_color = _styles.get('text_color', '#000000')
        font_size = _styles.get('font_size', 14)
        font_path = _styles.get('font', None)
        if font_path:
            fonts_dir = os.path.dirname(fonts.__file__)
            full_path = os.path.join(fonts_dir, os.path.basename(font_path))
            font = ImageFont.truetype(full_path, font_size)
        else:
            font = ImageFont.load_default()

        img_size = (2 * width, 2 * height)
        img = Image.new("RGBA", img_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle(
            (0, 0, img_size[0] - 1, img_size[1] - 1),
            radius=corner_radius * 2,
            outline=border_color,
            width=border_width * 2,
            fill=color
        )

        # inner border
        offset = border_width * 2
        draw.rounded_rectangle(
            (offset, offset, img_size[0] - 1 - offset, img_size[1] - 1 - offset),
            radius=corner_radius * 2,
            outline=inner_border_color,
            width=inner_border_width * 2
        )

        img = img.resize((width, height), Image.Resampling.LANCZOS)

        #   add icon
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
            max_icon_width = width - 2 * (border_width + inner_border_width)
            max_icon_height = height - 2 * (border_width + inner_border_width)

            if icon_resizable:
                _icon.thumbnail((max_icon_width, max_icon_height), Image.Resampling.LANCZOS)
                icon_w, icon_h = _icon.size
            else:
                if icon_w > max_icon_width or icon_h > max_icon_height:
                    _icon.thumbnail((max_icon_width, max_icon_height), Image.Resampling.LANCZOS)
                    icon_w, icon_h = _icon.size

            position = ((width - icon_w) // 2, (height - icon_h) // 2)

            if _icon.mode == 'RGBA':
                img.paste(_icon, position, mask=_icon)
            else:
                img.paste(_icon, position)

        #   add text
        if text:
            draw = ImageDraw.Draw(img)

            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            text_width, text_height = right - left, bottom - top

            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2

            draw.text((text_x, text_y), text, fill=text_color, font=font)

        return ctk.CTkImage(img, size=(width, height))

