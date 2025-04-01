import math
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import json
from pathlib import Path
# TO DO: Fix moving big images; fix maximize, fix set scale

root_folder = Path(__file__).parents[1]
themes_path = root_folder / "resources/theme.json"
ctk.set_default_color_theme(themes_path)

# Загружаем JSON-тему
with open(themes_path, "r") as file:
    theme = json.load(file)

def apply_theme(widget, widget_type):
    print(f'apply {widget}')
    widget_settings = theme.get(widget_type, {})
    try:
        widget.params = widget_settings['params']
    except:
        pass

    for param, value in widget_settings.items():
        if hasattr(widget, "configure") and param != 'params':
            try:
                widget.configure(**{param: value})
                widget.update()
                print(f'param: { param}; value: {value}')
            except Exception as e:
                print(f"Не удалось применить параметр '{param}': {e}")


class AutoScrollbar(ctk.CTkScrollbar):
    def __init__(self, _master, **kwargs):
        super().__init__(_master, **kwargs)
        apply_theme(self, "AutoScrollbar")
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            ctk.CTkScrollbar.set(self, lo, hi)
            self.grid()


class ImageCanvas(ctk.CTkFrame):
    def __init__(self, _master, _grid_state=False, _zoom_delta=5):
        super().__init__(_master)
        apply_theme(_master, "ImageCanvas")

        frame_border = theme.get("ImageCanvas", {})["border_width"]

        # Vertical and horizontal scrollbars for canvas
        vbar = AutoScrollbar(self.master, orientation='vertical', border_spacing=0, width=8)
        hbar = AutoScrollbar(self.master, orientation='horizontal', border_spacing=0, height=8)
        vbar.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky='ns')
        hbar.grid(row=1, column=0, padx=(0, 0), pady=(0, 0), sticky='we')

        # Init canvas
        self.canvas = ctk.CTkCanvas(self.master, highlightthickness=0, xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, padx=(8, 8), pady=(8, 8), sticky='nswe')
        self.canvas.update()  # wait until canvas is created

        # Move canvas in pixels
        self.canvas.configure(xscrollincrement=1, yscrollincrement=1)

        # Bind scrollbars to the canvas
        vbar.configure(command=self.scroll_y)
        hbar.configure(command=self.scroll_x)

        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Bind events to the Canvas
        self.canvas.bind('<MouseWheel>', self.wheel)
        # self.canvas.bind('<Button-2>', self.click)

        # Init start fields
        self.base_img = None
        self.img = None  # img to render
        self.draw = None
        self.base_width, self.base_height = None, None
        self.scaled_width, self.scaled_height = None, None
        self.tile = None
        self.scale = 1  # scale is 100%
        self.delta = _zoom_delta  # zoom magnitude
        self.offset = (0, 0)
        self.is_decreased = False  # is decreased
        self.interpolation = Image.Resampling.NEAREST  # interpolation method
        self.cursor_position = None
        self.frame_move = (0, 0)

    # Set an _img to ImageCanvas
    def set_image(self, _img: Image):
        try:
            if _img is not None:
                self.base_img = _img
                self.img = self.base_img.convert('RGBA')
                self.draw = ImageDraw.Draw(self.img)
                self.base_width, self.base_height = self.img.size
                self.scaled_width, self.scaled_height = round(self.scale * self.base_width - 1), round(self.scale * self.base_height - 1)

                self.tile = (self.base_width, self.base_height)
                imagetk = ImageTk.PhotoImage(self.img)
                imageid = self.canvas.create_image((0, 0), anchor='nw', image=imagetk, tag="img")
                self.canvas.tag_lower(imageid)
                self.canvas.imagetk = imagetk

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

                # red square at 0 0
                start = Image.new('RGB', (10, 10), (255, 0, 0))
                imagetk1 = ImageTk.PhotoImage(start)
                imageid1 = self.canvas.create_image((0, 0), anchor='nw', image=imagetk1, tag="img1")
                self.canvas.tag_raise(imageid1)
                self.canvas.imagetk1 = imagetk1

                self.canvas.update()
        except Exception as ex:
            print(ex)

    def maximize_image(self):
        canvas_box = (self.canvas.canvasx(0),
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        canvas_size = canvas_box[2] - canvas_box[0], canvas_box[3] - canvas_box[1]
        width_scale = canvas_size[0] / self.base_width
        height_scale = canvas_size[1] / self.base_height

        if width_scale * self.base_height > canvas_size[1]:
            width_scale = 0
        if height_scale * self.base_width > canvas_size[0]:
            height_scale = 0

        scale = max(width_scale, height_scale)
        if scale > 1:
            scale = int(scale)
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

    def wheel(self, event):
        print("wheel")
        if self.base_img is None:
            return
        x = self.canvas.canvasx(event.x)     # get cursor position before resizing
        y = self.canvas.canvasy(event.y)

        x_base, y_base = x / self.scale, y / self.scale

        img_box = (0, 0, self.scaled_width-1, self.scaled_height-1)  # get img area

        # if img_box[0] < x < img_box[2] and img_box[1] < y < img_box[3]:     # cursor out of the img
        #     pass
        # else:
        #     return

        if event.delta == -120:  # scroll down
            if self.scale - self.delta >= 1:
                self.scale -= self.delta
            elif (self.base_width * self.scale / 2 > 30) and (self.base_height * self.scale / 2 > 30):
                self.scale /= 2

        if event.delta == 120:  # scroll up
            if self.scale >= 1:
                self.scale += self.delta
            else:
                self.scale *= 2

        x_new, y_new = x_base * self.scale, y_base * self.scale
        self.frame_move = (int(x_new - x), int(y_new - y))

        self.scaled_width, self.scaled_height = round(self.scale * self.base_width), round(self.scale * self.base_height)
        self.canvas.configure(confine=False)

        self.canvas.xview_scroll(self.frame_move[0], ctk.UNITS)
        self.canvas.yview_scroll(self.frame_move[1], ctk.UNITS)

        if self.scale >= 1:
            self.interpolation = Image.Resampling.NEAREST  # img is increased
        else:
            self.interpolation = Image.Resampling.LANCZOS  # img is decreased

        self.render()

    # def click(self, event):
    #     print("click")
    #     x = self.canvas.canvasx(event.x)  # get cursor position
    #     y = self.canvas.canvasy(event.y)
    #
    #     base_x = x // self.scale
    #     base_y = y // self.scale
    #     print(f'cursor_position: {x, y}')
    #     print(f'pixel_pos: {base_x, base_y}')
    #     print(f'frame_move: {self.frame_move}')
    #
    #     self.canvas.xview_scroll(30, ctk.UNITS)
    #     self.canvas.yview_scroll(50, ctk.UNITS)

    def render(self, event=None):
        if self.base_img is None:
            return

        # границы отмасштабированного изображения
        img_box = (0, 0, self.scaled_width - 1, self.scaled_height - 1)

        # кадрирующее окно
        canvas_box = (self.canvas.canvasx(0),
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))

        print(f"scale: {self.scale}")
        # print(f'scaled size: {self.scaled_width}:{self.scaled_height}')
        # print(f'move_vector: {self.frame_move}')
        # print(f'canvas_box: {canvas_box}\n img_box: {img_box}\n')

        # область пересечения окна и отмасштабированного изображения
        x1 = max(canvas_box[0], 0)
        y1 = max(canvas_box[1], 0)
        x2 = min(canvas_box[2], img_box[2])
        y2 = min(canvas_box[3], img_box[3])

        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # if visible

            # область пересечения на исходном изображении
            x1_base = max(int(x1 / self.scale), 0)
            y1_base = max(int(y1 / self.scale), 0)
            x2_base = min(math.ceil(x2 / self.scale), self.base_width - 1)
            y2_base = min(math.ceil(y2 / self.scale), self.base_height - 1)

            # размеры области пересечения на исходном изображении
            x_base_delta = x2_base - x1_base
            y_base_delta = y2_base - y1_base

            start_point_x_scaled = x1 % self.scale
            start_point_y_scaled = y1 % self.scale
            end_point_x_scaled = start_point_x_scaled + math.ceil(x2 - x1)
            end_point_y_scaled = start_point_y_scaled + math.ceil(y2 - y1)

            base_img_segment = self.img.crop((x1_base, y1_base, x2_base, y2_base))

            img_segment = base_img_segment.resize((int(x_base_delta * self.scale), int(y_base_delta * self.scale)), self.interpolation)
            result_img = img_segment.crop((start_point_x_scaled, start_point_y_scaled, end_point_x_scaled, end_point_y_scaled))

            imagetk = ImageTk.PhotoImage(result_img)
            self.offset = (x1, y1)
            imageid = self.canvas.create_image(self.offset, anchor='nw', image=imagetk, tag="img")
            self.canvas.tag_lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

            self.canvas.configure(scrollregion=(0, 0, self.scaled_width - 1, self.scaled_height - 1))
            self.frame_move = (0, 0)


# root = ctk.CTk()
#
# img = Image.open("img.png")
# img.putpixel((x, y), (0, 0, 0))
# img_canvas = ImageCanvas(root)
# img_canvas.set_image(img)
#
# root.mainloop()
