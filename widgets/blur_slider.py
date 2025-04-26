import customtkinter as ctk
from widgets.base import BaseWidget
from colorsys import rgb_to_hsv, hsv_to_rgb
from utils.color_models import rgb2hex, hex2rgb
from utils.figures import draw_ellipse

from PIL import Image, ImageDraw, ImageTk
import colorsys




class BlurSlider(BaseWidget, ctk.CTkCanvas):

    binds = {"<Button-1>": "on_click", "<B1-Motion>": "on_drag"}

    def __init__(self, master, _event_bus, _is_last=False, **kwargs):
        ctk.CTkCanvas.__init__(self, master=master, height=20, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        self.pointer_pos = 0
        self.build_view()

        if _is_last:
            self.init_subscribes()

    def build_view(self):
        self.width = self.additional_styles.get("width", 100)
        self.height = self.additional_styles.get("height", 20)
        self.border_width = self.additional_styles.get("border_width", 0)
        self.border_color = self.additional_styles.get("border_color", "#ffffff")
        self.pointer_color = self.additional_styles.get("pointer_color", "#ffffff")
        self.pointer_radius = self.additional_styles.get("pointer_radius", 8)
        self.pointer_border = self.additional_styles.get("pointer_border", 3)
        self.pointer_border_color = self.additional_styles.get("pointer_border_color", "#ffffff")
        self.bar_color = self.additional_styles.get("bar_color", "#303030")
        self.bg_color = self.additional_styles.get("bg_color", "#303030")
        self.configure(width=self.width, height=self.height)
        self.grid_propagate(False)
        self.configure(borderwidth=0, highlightthickness=self.border_width, highlightbackground=self.border_color, bg=self.bg_color)
        self.bar_img = self.build_bar()
        bar_img = ImageTk.PhotoImage(self.bar_img)
        self._bar_img_ref = bar_img  # сохранить ссылку
        self.create_image(0, 0, anchor="nw", image=self._bar_img_ref)


        pointer_img = Image.new("RGBA", (self.pointer_radius * 2, self.pointer_radius * 2), (0, 0, 0, 0))

        self.circle = draw_ellipse(pointer_img,
                              [self.pointer_border, self.pointer_border, 2 * self.pointer_radius - self.pointer_border,
                               2 * self.pointer_radius - self.pointer_border], width=self.pointer_border,
                              fillcolor=self.pointer_color, outlinecolor=self.pointer_border_color)
        self.pointer_img = ImageTk.PhotoImage(image= self.circle)
        self._pointer_img_ref = self.pointer_img
        self.update_slider()

    def build_bar(self):
        rgb = hex2rgb(self.bar_color)
        base_img = Image.new("RGB", (self.pointer_pos, self.height), color=rgb)
        return base_img

    def update_slider(self):
        # pointer_pos = int(self.pointer_pos / 255 * (self.width - 1))
        # # pointer_pos = max(self.pointer_radius, min(pointer_pos, self.height - 1 - self.pointer_radius))
        # pointer_pos = max(self.pointer_radius, min(pointer_pos, self.width - 1 - self.pointer_radius))
        #
        # bounds = (
        #     pointer_pos - self.pointer_radius,
        #     self.width // 2 - self.pointer_radius)
        #
        # bar_img = self.build_bar()
        # self.bar_img = ImageTk.PhotoImage(image= bar_img)
        # self.delete("all")
        # self.create_image((self.border_width, self.border_width), anchor="nw", image=self.bar_img)
        # self.create_image(bounds, anchor="nw", image=self.pointer_img)

        pointer_pos = int(self.pointer_pos / 255 * (self.width - 1))
        pointer_pos = max(self.pointer_radius, min(pointer_pos, self.width - 1 - self.pointer_radius))
        # pointer_pos = max(self.pointer_radius, min(pointer_pos, self.height - 1 - self.pointer_radius))
        bounds = (
            pointer_pos - self.pointer_radius,
            self.height // 2 - self.pointer_radius + self.border_width
        )

        bar_img = self.build_bar()
        self.bar_img = ImageTk.PhotoImage(image=bar_img)
        self.pointer_img = ImageTk.PhotoImage(image= self.circle)

        self._bar_img_ref = self.bar_img
        self._pointer_img_ref = self.pointer_img

        self.delete("all")
        self.create_image((self.border_width, self.border_width), anchor="nw", image=self._bar_img_ref)
        self.create_image(bounds, anchor="nw", image=self._pointer_img_ref)



    def on_click(self, event):
        width = self.winfo_width() or 256

        raw_pos = min(max(event.x, 0), width - 1)
        self.pointer_pos = int((raw_pos / (width - 1)) * 255)

        self.update_slider()
        self.change_blur()

    def on_drag(self, event):
        self.on_click(event)

    def change_blur(self):
        self.event_bus.send_state("blur_changed", int(self.pointer_pos / 10))
        print(self.pointer_pos)