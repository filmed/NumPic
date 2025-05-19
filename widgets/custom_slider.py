import customtkinter as ctk
from widgets.base import BaseWidget
from utils.color_models import hex2rgb
from utils.figures import draw_ellipse
from PIL import Image, ImageTk


class CustomSlider(BaseWidget, ctk.CTkCanvas):
    binds = {"<Button-1>": "on_click", "<B1-Motion>": "on_drag"}

    def __init__(self, master, _event_bus, _is_last=False, from_=0, to=100, step=1, command=None, **kwargs):
        ctk.CTkCanvas.__init__(self, master=master, height=20, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.from_ = from_
        self.to = to
        self.step = step
        self.command = command
        self.value = self.from_
        self.pointer_pos = 0 #0-1

        self.build_view()

        if _is_last:
            self.init_subscribes()

    def build_view(self):
        styles = self.additional_styles
        self.width = styles.get("width", 100)
        self.height = styles.get("height", 20)
        self.border_width = styles.get("border_width", 0)
        self.border_color = styles.get("border_color", "#ffffff")
        self.pointer_color = styles.get("pointer_color", "#ffffff")
        self.pointer_radius = styles.get("pointer_radius", 8)
        self.pointer_border = styles.get("pointer_border", 3)
        self.pointer_border_color = styles.get("pointer_border_color", "#ffffff")
        self.bar_color = styles.get("bar_color", "#303030")
        self.bg_color = styles.get("bg_color", "#303030")

        self.configure(
            width=self.width,
            height=self.height,
            borderwidth=0,
            highlightthickness=self.border_width,
            highlightbackground=self.border_color,
            bg=self.bg_color
        )
        self.grid_propagate(False)
        self._draw_static_bar()
        self._prepare_pointer_image()
        self.update_slider()

    def _draw_static_bar(self):
        bar_image = Image.new("RGB", (self.width, self.height), color=hex2rgb(self.bar_color))
        self._bar_img_ref = ImageTk.PhotoImage(bar_image)
        self.create_image(0, 0, anchor="nw", image=self._bar_img_ref)

    def _prepare_pointer_image(self):
        diameter = self.pointer_radius * 2
        pointer_img = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
        pointer_img = draw_ellipse(
            pointer_img,
            [self.pointer_border, self.pointer_border, diameter - self.pointer_border, diameter - self.pointer_border],
            width=self.pointer_border,
            fillcolor=self.pointer_color,
            outlinecolor=self.pointer_border_color
        )
        self._pointer_img_ref = ImageTk.PhotoImage(pointer_img)

    def _build_bar_image(self, fill_width):
        bar_img = Image.new("RGB", (self.width, self.height), hex2rgb(self.bg_color))
        draw = Image.new("RGB", (fill_width, self.height), hex2rgb(self.bar_color))
        bar_img.paste(draw, (0, 0))
        return ImageTk.PhotoImage(bar_img)

    def update_slider(self):
        self.delete("all")
        fill_width = int(self.pointer_pos * self.width)
        fill_width = max(0, min(fill_width, self.width))
        bar_image = self._build_bar_image(fill_width)
        self._bar_img_ref = bar_image
        self.create_image((self.border_width, self.border_width), anchor="nw", image=self._bar_img_ref)

        pos_x = max(self.pointer_radius, min(fill_width, self.width - self.pointer_radius))
        pos_y = self.height // 2 - self.pointer_radius + self.border_width
        self.create_image(pos_x - self.pointer_radius, pos_y, anchor="nw", image=self._pointer_img_ref)

    def on_click(self, event):
        width = self.winfo_width() or 256
        rel = min(max(event.x, 0), width - 1) / (width - 1)
        self.pointer_pos = rel

        raw_value = self.from_ + (self.to - self.from_) * rel
        stepped = round(raw_value / self.step) * self.step
        stepped = min(max(self.from_, stepped), self.to)

        self.value = stepped
        self.update_slider()

        if self.command:
            self.command(self.value)

    def on_drag(self, event):
        self.on_click(event)

    def set(self, value: float):
        value = min(max(value, self.from_), self.to)
        self.value = value
        rel = (value - self.from_) / (self.to - self.from_)
        self.pointer_pos = rel
        self.update_slider()