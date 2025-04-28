import customtkinter as ctk
from widgets.base import BaseWidget
from colorsys import rgb_to_hsv, hsv_to_rgb
from utils.color_models import rgb2hex, hex2rgb
from utils.figures import draw_ellipse

from PIL import Image, ImageDraw, ImageTk
import colorsys

class ColorSlider(BaseWidget, ctk.CTkCanvas):

    binds = {"<Button-1>": "on_click", "<B1-Motion>": "on_drag", "<Configure>": "on_resize"}

    def __init__(self, master, _event_bus, channel: str, _is_last=False, **kwargs):
        ctk.CTkCanvas.__init__(self, master=master, height=20, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.channel = channel.lower()  # 'r', 'g', 'b', 'h', 's', 'v'
        self.pointer_pos = 0
        self.pointer_radius = 8
        self.pointer_border = 3
        self.gradient_img = None

        self.build_view()

        if _is_last:
            self.init_subscribes()

    def build_view(self):
        self.width = self.additional_styles.get("width", 100)
        self.height = self.additional_styles.get("height", 20)
        self.border_width = self.additional_styles.get("border_width", 0)
        self.border_color = self.additional_styles.get("border_color", "#ffffff")
        self.configure(width=self.width, height=self.height)
        self.grid_propagate(False)
        self.configure(borderwidth=0, highlightthickness=self.border_width, highlightbackground=self.border_color)

    def on_resize(self, event):
        if hasattr(self, 'current_color') and hasattr(self, 'color_type'):
            self.update_slider(self.current_color, self.color_type)

    def build_gradient(self, base_color, color_type):
        base_width = 10
        height = self.winfo_height() or 20

        base_img = Image.new("RGB", (base_width, 1))
        pixels = base_img.load()

        if color_type == "RGB":
            r, g, b = base_color
            for x in range(base_width):
                value = int(x / (base_width - 1) * 255)
                if self.channel == "r":
                    px_color = (value, g, b)
                elif self.channel == "g":
                    px_color = (r, value, b)
                else:  # 'b'
                    px_color = (r, g, value)
                pixels[x, 0] = px_color
        else:
            h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in base_color])
            for x in range(base_width):
                value = x / (base_width - 1)
                if self.channel == "h":
                    px_hsv = (value * 360, s, v)
                elif self.channel == "s":
                    px_hsv = (h, value, v)
                else:  # 'v'
                    px_hsv = (h, s, value)

                r, g, b = colorsys.hsv_to_rgb(*px_hsv)
                pixels[x, 0] = (int(r * 255), int(g * 255), int(b * 255))

        width = self.winfo_width() or 256
        return base_img.resize((width, height), Image.Resampling.BILINEAR)

    def update_slider(self, color, color_type):
        self.current_color = color
        self.color_type = color_type

        gradient_img = self.build_gradient(color, color_type)
        width, height = gradient_img.size

        pointer_img = Image.new("RGBA", (self.pointer_radius*2, self.pointer_radius*2), (0, 0, 0, 0))

        circle = draw_ellipse(pointer_img,
                              [self.pointer_border, self.pointer_border, 2*self.pointer_radius - self.pointer_border,
                               2*self.pointer_radius - self.pointer_border], width=self.pointer_border,
                              fillcolor=self.current_color, outlinecolor="#ffffffff")
        self.pointer_img = ImageTk.PhotoImage(image=circle)

        pointer_pos = int(self.pointer_pos / 255 * (width - 1))
        pointer_pos = max(self.pointer_radius, min(pointer_pos, width - 1 - self.pointer_radius))

        bounds = (
            pointer_pos - self.pointer_radius,
            height // 2 - self.pointer_radius)

        gradient_img = gradient_img.convert("RGBA")

        self.gradient_img = ImageTk.PhotoImage(gradient_img)
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self.gradient_img)
        self.create_image(bounds, anchor="nw", image=self.pointer_img)


    def on_click(self, event):
        width = self.winfo_width() or 256

        raw_pos = min(max(event.x, 0), width - 1)
        self.pointer_pos = int((raw_pos / (width - 1)) * 255)

        self.update_slider(self.current_color, self.color_type)
        self.emit_color()

    def on_drag(self, event):
        self.on_click(event)

    def set_position_from_color(self, color, color_type):
        if color_type == "RGB":
            rgb = color
            channel_map = {"r": 0, "g": 1, "b": 2}
            if self.channel in channel_map:
                self.pointer_pos = rgb[channel_map[self.channel]]
        else:  # HSV
            h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in color])
            if self.channel == "h":
                self.pointer_pos = int(h * 255)
            elif self.channel == "s":
                self.pointer_pos = int(s * 255)
            elif self.channel == "v":
                self.pointer_pos = int(v * 255)

        if hasattr(self, 'current_color') and hasattr(self, 'color_type'):
            self.update_slider(self.current_color, self.color_type)

    def emit_color(self):
        if not hasattr(self.master, 'sliders'):
            return

        if self.master.color_type == "RGB":
            r = round((self.master.sliders["r"].pointer_pos))
            g = round(self.master.sliders["g"].pointer_pos)
            b = round(self.master.sliders["b"].pointer_pos)
            hex_color = rgb2hex((r, g, b))
        else:  # HSV
            h = self.master.sliders["h"].pointer_pos / 255 * 360
            s = self.master.sliders["s"].pointer_pos / 255
            v = self.master.sliders["v"].pointer_pos / 255
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h / 360, s, v)]
            hex_color = rgb2hex((r, g, b))

        self.event_bus.send_state("color_modify", hex_color.upper())


class PalletSlidersFrame(BaseWidget, ctk.CTkFrame):
    subscriptions = {"color_changed": "on_color_changed"}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkFrame.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.color_type = "RGB"  # По умолчанию RGB
        self.sliders = {}
        self.current_color = "#000000"

        self.refresh_sliders()
        self.columnconfigure(0, weight=1)
        self.configure(fg_color="transparent")

        if _is_last:
            self.init_subscribes()

    def set_color_type(self, color_type):
        if color_type.upper() in ("RGB", "HSV") and self.color_type != color_type:
            self.color_type = color_type.upper()
            self.refresh_sliders()

    def refresh_sliders(self):
        self.clear_sliders()

        channels = "rgb" if self.color_type == "RGB" else "hsv"
        rgb_color = hex2rgb(self.current_color)

        for i, ch in enumerate(channels):
            slider = ColorSlider(self, self.event_bus, channel=ch, _is_last=True)
            slider.grid(row=i, column=0, padx=0, pady=5, sticky="")
            slider.update_slider(rgb_color, self.color_type)
            slider.set_position_from_color(rgb_color, self.color_type)
            self.sliders[ch] = slider

    def clear_sliders(self):
        for slider in self.sliders.values():
            slider.destroy()
        self.sliders = {}

    def on_color_changed(self, color: str):
        if color.startswith("#"):
            self.current_color = color
            rgb_color = hex2rgb(color)
            for slider in self.sliders.values():
                slider.update_slider(rgb_color, self.color_type)
                slider.set_position_from_color(rgb_color, self.color_type)