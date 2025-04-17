import customtkinter as ctk
from widgets.base import BaseWidget
from utils.figures import draw_ellipse
from colorsys import rgb_to_hsv, hsv_to_rgb
from utils.color_models import rgb2hex, hex2rgb
from PIL import Image, ImageTk
import colorsys


class ColorSlider(BaseWidget, ctk.CTkCanvas):
    def __init__(self, master, _event_bus, channel: str, **kwargs):
        ctk.CTkCanvas.__init__(self, master=master, height=20, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.channel = channel.lower()  # 'r', 'g', 'b', 'h', 's', 'v'
        self.pointer_pos = 0
        self.gradient_img = None
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)

    def build_gradient(self, base_color, color_type):
        """Создает градиентную полосу в зависимости от типа цветового пространства"""
        width = self.winfo_width() or 256
        img = Image.new("RGB", (width, 1))
        pixels = img.load()

        if color_type == "RGB":
            r, g, b = base_color
            for x in range(width):
                value = int(x / width * 255)
                if self.channel == "r":
                    px_color = (value, g, b)
                elif self.channel == "g":
                    px_color = (r, value, b)
                else:  # 'b'
                    px_color = (r, g, value)
                pixels[x, 0] = px_color
        else:  # HSV
            h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in base_color])
            for x in range(width):
                value = x / width
                if self.channel == "h":
                    px_hsv = (value * 360, s, v)
                elif self.channel == "s":
                    px_hsv = (h, value, v)
                else:  # 'v'
                    px_hsv = (h, s, value)

                r, g, b = colorsys.hsv_to_rgb(*px_hsv)
                pixels[x, 0] = (int(r * 255), int(g * 255), int(b * 255))

        return ImageTk.PhotoImage(img.resize((width, 20)))

    def update_slider(self, color, color_type):
        """Обновляет градиент и позицию указателя"""
        self.gradient_img = self.build_gradient(color, color_type)
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self.gradient_img)
        self.draw_pointer()

    def draw_pointer(self):
        """Рисует указатель на текущей позиции"""
        self.delete("pointer")
        x = self.pointer_pos * (self.winfo_width() - 1) / 255
        draw_ellipse(self, x, 10, 6, 6, tag="pointer", fill="white", outline="black")

    def on_click(self, event):
        """Обработчик клика мыши"""
        self.pointer_pos = min(max(event.x, 0), self.winfo_width() - 1) * 255 / (self.winfo_width() - 1)
        self.draw_pointer()
        self.emit_color()

    def on_drag(self, event):
        """Обработчик перемещения мыши с зажатой кнопкой"""
        self.on_click(event)

    def set_position_from_color(self, color, color_type):
        """Устанавливает позицию указателя на основе цвета"""
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
        self.draw_pointer()

    def emit_color(self):
        """Отправляет текущий цвет через event_bus"""
        if not hasattr(self.master, 'sliders'):
            return

        if self.master.color_type == "RGB":
            r = self.master.sliders["r"].pointer_pos
            g = self.master.sliders["g"].pointer_pos
            b = self.master.sliders["b"].pointer_pos
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
        else:  # HSV
            h = self.master.sliders["h"].pointer_pos / 255 * 360
            s = self.master.sliders["s"].pointer_pos / 255
            v = self.master.sliders["v"].pointer_pos / 255
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h / 360, s, v)]
            hex_color = f"#{r:02x}{g:02x}{b:02x}"

        self.event_bus.send_state("color_modify", hex_color.upper())


class ColorSlidersFrame(BaseWidget, ctk.CTkFrame):
    subscriptions = {"color_changed": "on_color_changed"}

    def __init__(self, master, _event_bus, **kwargs):
        ctk.CTTkFrame.__init__(self, master=master, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.color_type = "RGB"  # По умолчанию RGB
        self.sliders = {}
        self.current_color = "#000000"

        # Создаем слайдеры для RGB по умолчанию
        self.refresh_sliders()
        self.columnconfigure(0, weight=1)

    def set_color_type(self, color_type):
        """Переключает между RGB и HSV режимами"""
        if color_type.upper() in ("RGB", "HSV") and self.color_type != color_type:
            self.color_type = color_type.upper()
            self.refresh_sliders()

    def refresh_sliders(self):
        """Обновляет слайдеры в соответствии с текущим цветовым пространством"""
        self.clear_sliders()

        channels = "rgb" if self.color_type == "RGB" else "hsv"
        rgb_color = hex2rgb(self.current_color)

        for i, ch in enumerate(channels):
            slider = ColorSlider(self, self.event_bus, channel=ch)
            slider.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            slider.update_slider(rgb_color, self.color_type)
            slider.set_position_from_color(rgb_color, self.color_type)
            self.sliders[ch] = slider

    def clear_sliders(self):
        """Удаляет все текущие слайдеры"""
        for slider in self.sliders.values():
            slider.destroy()
        self.sliders = {}

    def on_color_changed(self, color: str):
        """Обработчик изменения цвета"""
        if color.startswith("#"):
            self.current_color = color
            rgb_color = hex2rgb(color)
            for slider in self.sliders.values():
                slider.update_slider(rgb_color, self.color_type)
                slider.set_position_from_color(rgb_color, self.color_type)