import os
from widgets.base import BaseWidget
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
import sprites
import fonts
import copy
from utils.figures import get_text_size


class CustomLabel(BaseWidget, ctk.CTkLabel):

    def __init__(self, master, _event_bus, _text, _is_last=False, **kwargs):
        ctk.CTkLabel.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)
        self.text = _text

        self.image_idle = self.build_view()
        self.configure(image=self.image_idle)

        if _is_last:
            self.init_subscribes()

    def build_view(self):
        color = self.additional_styles.get('color', '#FF000000')
        border_color = self.additional_styles.get('border_color', '#FFFFFF')
        inner_border_color = self.additional_styles.get('inner_border_color', '#000000')
        border_width = self.additional_styles.get('border_width', 0)
        inner_border_width = self.additional_styles.get('inner_border_width', 0)
        corner_radius = self.additional_styles.get('corner_radius', 5)

        text_color = self.additional_styles.get('text_color', '#000000')
        font_size = self.additional_styles.get('font_size', 14)
        font_path = self.additional_styles.get('font', None)
        if font_path:
            fonts_dir = os.path.dirname(fonts.__file__)
            full_path = os.path.join(fonts_dir, os.path.basename(font_path))
            font = ImageFont.truetype(full_path, font_size)
        else:
            font = ImageFont.load_default()

        bbox = font.getbbox(self.text)

        text_width, text_height = int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])

        width, height = text_width + 2 * (border_width + inner_border_width), text_height + 2 * (border_width + inner_border_width)

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

        draw = ImageDraw.Draw(img)

        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2

        draw.text((text_x, text_y),  self.text, fill=text_color, font=font, anchor="lt")

        return ctk.CTkImage(img, size=(width, height))
