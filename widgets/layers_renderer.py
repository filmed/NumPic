import customtkinter as ctk
from widgets.base import BaseWidget
from widgets.auto_scroll_bar import AutoScrollbar
from PIL import Image, ImageDraw, ImageTk
import math
from core.layer_manager import LayerManager
from core.models import filters


class LayersRenderer(BaseWidget, ctk.CTkFrame):

    subscriptions = {"layer_inited": "on_layer_inited", "layer_selected": "on_layer_changed", "filter_params_updated": "on_filter_updated"}
    binds = {**BaseWidget.binds}

    def __init__(self, master, _event_bus, _layer_manager:LayerManager, _zoom_delta=5, _is_last=False, fixed_size=None, **kwargs):
        self.fixed_width = kwargs.pop("width", 0)
        self.fixed_height = kwargs.pop("height", 0)

        ctk.CTkFrame.__init__(self, master=master, width=self.fixed_width, height=self.fixed_height, **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)

        if self.fixed_width and self.fixed_height:
            self.grid_propagate(False)

        # Vertical and horizontal scrollbars for canvas
        vbar = AutoScrollbar(self, self.event_bus, orientation='vertical', border_spacing=0, width=8)
        hbar = AutoScrollbar(self,  self.event_bus, orientation='horizontal', border_spacing=0, height=8)
        vbar.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky='nsw')
        hbar.grid(row=1, column=0, padx=(0, 0), pady=(0, 0), sticky='wen')

        self.outline = ctk.CTkFrame(self)
        self.outline.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="nsew")
        self.outline.rowconfigure(0, weight=1)
        self.outline.columnconfigure(0, weight=1)

        self.canvas_container = ctk.CTkFrame(self.outline)
        self.canvas_container.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="nsew")
        self.canvas_container.rowconfigure(0, weight=1)
        self.canvas_container.columnconfigure(0, weight=1)

        # Init canvas
        self.canvas = ctk.CTkCanvas(self.canvas_container, highlightthickness=0, xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait until canvas is created

        # Move canvas in pixels
        self.canvas.configure(xscrollincrement=1, yscrollincrement=1)
        self.canvas.configure(confine=False)

        # Bind scrollbars to the canvas
        vbar.configure(command=self.scroll_y)
        hbar.configure(command=self.scroll_x)

        # Make the canvas expandable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Bind events to the !Canvas!
        self.canvas.bind('<MouseWheel>', self.on_wheel, add="+")
        self.canvas.bind('<Enter>', self.on_enter, add="+")

        # Init start fields
        self.layer_manager = _layer_manager
        self.cache_before = None
        self.cache_after = None
        self.current_layer = None
        self.composited_img = None
        self.checkerboard_bg = None

        self.cursor_drawer = None
        self.cursor_id = None

        self.draw = None
        self.base_width, self.base_height = None, None
        self.scaled_width, self.scaled_height = None, None
        self.scale = 1  # scale is 100%
        self.delta = _zoom_delta  # zoom magnitude
        self.interpolation = Image.Resampling.NEAREST  # interpolation method

        self.build_view()

        if _is_last:
            self.init_subscribes()

    def build_view(self):
        canvas_bg = self.additional_styles.get("canvas_bg", "#828282")

        out_border_width = self.additional_styles.get("out_border_width", 0)
        mid_border_width = self.additional_styles.get("mid_border_width", 0)
        inner_border_width = self.additional_styles.get("inner_border_width", 0)

        out_border_color = self.additional_styles.get("out_border_color", "#000000")
        mid_border_color = self.additional_styles.get("mid_border_color", "#000000")
        inner_border_color = self.additional_styles.get("inner_border_color", "#000000")

        self.outline.configure(fg_color=out_border_color)
        self.canvas_container.configure(fg_color=mid_border_color)
        self.canvas_container.grid_configure(padx=out_border_width, pady=out_border_width)
        self.canvas.configure(highlightthickness=inner_border_width, highlightbackground=inner_border_color)
        self.canvas.grid_configure(padx=mid_border_width, pady=mid_border_width)
        self.canvas.configure(bg=canvas_bg)

    # Send current use zone
    def on_enter(self, event=None):
        self.event_bus.send_state('use_zone_changed', self)


    def on_layer_inited(self, _layer=None):
        if _layer is None:
            return
        self.current_layer = _layer
        self.update_cache()
        self.draw = ImageDraw.Draw(self.current_layer.img)
        self.base_width, self.base_height = self.current_layer.img.size
        self.scaled_width, self.scaled_height = round(self.scale * self.base_width - 1), round(self.scale * self.base_height - 1)

        self.checkerboard_bg = self.create_checkerboard(self.base_width, self.base_height)
        imagetk = ImageTk.PhotoImage(self.current_layer.img)
        imageid = self.canvas.create_image((0, 0), anchor='nw', image=imagetk, tag="img")
        self.canvas.tag_lower(imageid)
        self.canvas.imagetk = imagetk

        if self.cursor_id is None:
            cursor_img = Image.new("RGBA", (10, 10), "black")
            cursortk = ImageTk.PhotoImage(cursor_img)
            self.cursor_id = self.canvas.create_image((0, 0), anchor='nw', image=cursortk, tag="cursor_icon")
            self.canvas.tag_raise(self.cursor_id)
            self.canvas.cursortk = cursortk

        canvas_box = (self.canvas.canvasx(0),
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))

        canvas_center = (canvas_box[0] + canvas_box[2]) / 2, (canvas_box[1] + canvas_box[3]) / 2

        self.maximize_image()

        image_center = self.scaled_width / 2, self.scaled_height / 2
        center_vec = int(canvas_center[0] - image_center[0]), int(canvas_center[1] - image_center[1])

        self.canvas.xview_scroll(-center_vec[0], ctk.UNITS)
        self.canvas.yview_scroll(-center_vec[1], ctk.UNITS)

        self.canvas.update()


    def maximize_image(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        highlight = int(self.canvas.cget("highlightthickness"))
        canvas_width -= 2 * highlight
        canvas_height -= 2 * highlight

        width_scale = canvas_width / self.base_width
        height_scale = canvas_height / self.base_height

        scale = min(width_scale, height_scale)

        # scale = max(scale, 1.0)

        self.set_scale(scale)

    def set_scale(self, _scale):
        self.scale = _scale
        self.scaled_width, self.scaled_height = round(self.scale * self.base_width), round(self.scale * self.base_height)
        self.render()

    def scroll_y(self, *args, **kwargs):
        self.canvas.yview(*args, **kwargs)
        self.render()

    def scroll_x(self, *args, **kwargs):
        self.canvas.xview(*args, **kwargs)
        self.render()

    def on_wheel(self, event):
        if self.current_layer is None:
            return
        highlight = int(self.canvas.cget("highlightthickness"))
        canvas_x = self.canvas.canvasx(event.x) - highlight
        canvas_y = self.canvas.canvasy(event.y) - highlight


        image_x = canvas_x / self.scale
        image_y = canvas_y / self.scale

        if event.delta == -120:  # отдаление
            if self.scale - self.delta >= 1:
                self.scale -= self.delta
            elif (self.base_width * self.scale / 2 > 30) and (self.base_height * self.scale / 2 > 30):
                self.scale /= 2
        elif event.delta == 120:  # приближение
            if self.scale >= 1:
                self.scale += self.delta
            else:
                self.scale *= 2

        self.scaled_width = round(self.base_width * self.scale)
        self.scaled_height = round(self.base_height * self.scale)

        new_canvas_x = image_x * self.scale
        new_canvas_y = image_y * self.scale

        dx = new_canvas_x - canvas_x
        dy = new_canvas_y - canvas_y

        self.canvas.configure(scrollregion=(0, 0, self.scaled_width, self.scaled_height))

        self.canvas.xview_moveto((self.canvas.canvasx(0) + highlight  + dx) / self.scaled_width)
        self.canvas.yview_moveto((self.canvas.canvasy(0) + highlight + dy) / self.scaled_height)

        if self.scale >= 1:
            self.interpolation = Image.Resampling.NEAREST
        else:
            self.interpolation = Image.Resampling.LANCZOS

        self.render()

    def on_layer_changed(self, _layer=None):
        if _layer is None:
            return
        self.current_layer = _layer
        self.update_cache()
        self.draw = ImageDraw.Draw(self.current_layer.img)
        self.render()

    def on_filter_updated(self, _data):
        if _data is None:
            return
        self.update_cache()
        self.render()

    def update_cache(self):
        self.composited_img = None
        current_index = self.layer_manager.current_index
        self.cache_before = self.layer_manager.get_merged(0, current_index)
        self.cache_after = self.layer_manager.get_merged(current_index+1, None)

    def get_composited_img(self):
        if self.current_layer is None:
            return

        if self.cache_before is None or self.cache_after is None:
            self.update_cache()

        result = Image.new("RGBA", self.current_layer.img.size, (0, 0, 0, 0))

        if self.cache_before:
            result.alpha_composite(self.cache_before)

        filtered_current = filters.apply_filters(self.current_layer.img, self.current_layer.filter_params)
        result.alpha_composite(filtered_current)

        if self.cache_after:
            result.alpha_composite(self.cache_after)


        return result

    def create_checkerboard(self, width, height, tile_size=10, color1 = (192, 192, 192),  color2 = (224, 224, 224)):
        checker = Image.new("RGB", (tile_size * 2, tile_size * 2), color1)
        draw = ImageDraw.Draw(checker)
        draw.rectangle([0, 0, tile_size - 1, tile_size - 1], fill=color2)
        draw.rectangle([tile_size, tile_size, tile_size * 2 - 1, tile_size * 2 - 1], fill=color2)

        bg = Image.new("RGB", (width, height))
        for y in range(0, height, tile_size * 2):
            for x in range(0, width, tile_size * 2):
                bg.paste(checker, (x, y))
        return bg.convert("RGBA")

    def render(self, event=None):
        if self.current_layer is None:
            return

        if self.composited_img is None:
            self.composited_img = self.get_composited_img()

        img_box = (0, 0, self.scaled_width, self.scaled_height)

        canvas_box = (
            self.canvas.canvasx(0),
            self.canvas.canvasy(0),
            self.canvas.canvasx(self.canvas.winfo_width() + 1),
            self.canvas.canvasy(self.canvas.winfo_height() + 1)
        )

        x1 = max(math.floor(canvas_box[0]), 0)
        y1 = max(math.floor(canvas_box[1]), 0)
        x2 = min(math.ceil(canvas_box[2]), img_box[2])
        y2 = min(math.ceil(canvas_box[3]), img_box[3])

        if (x2 - x1) >= 1 and (y2 - y1) >= 1:
            x1_base = max(int(x1 / self.scale), 0)
            y1_base = max(int(y1 / self.scale), 0)
            x2_base = min(math.ceil(x2 / self.scale), self.base_width)
            y2_base = min(math.ceil(y2 / self.scale), self.base_height)

            bg_segment = self.checkerboard_bg.crop((x1_base, y1_base, x2_base, y2_base))
            base_img_segment = self.composited_img.crop((x1_base, y1_base, x2_base, y2_base))
            base_img_segment = Image.alpha_composite(bg_segment, base_img_segment)
            img_segment = base_img_segment.resize(
                (int((x2_base - x1_base) * self.scale),
                 int((y2_base - y1_base) * self.scale)),
                self.interpolation
            )

            offset_x = x1 % self.scale
            offset_y = y1 % self.scale


            result_img = img_segment.crop((offset_x, offset_y, offset_x + (x2 - x1), offset_y + (y2 - y1)))

            imagetk = ImageTk.PhotoImage(result_img)
            self.canvas.delete("img")
            self.canvas.create_image(x1, y1, anchor='nw', image=imagetk, tag="img")
            self.canvas.imagetk = imagetk

        self.canvas.configure(scrollregion=(0, 0, self.scaled_width, self.scaled_height))
        self.event_bus.send_state("canvas_rendered", True)