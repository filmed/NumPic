import math
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw


class AutoScrollbar(ctk.CTkScrollbar):
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ctk.CTkScrollbar.set(self, lo, hi)


class ImageCanvas(ctk.CTkFrame):
    def __init__(self, _master, _grid_state=False, _zoom_delta=1):
        ctk.CTkFrame.__init__(self, master=_master)

        # Vertical and horizontal scrollbars for canvas
        vbar = AutoScrollbar(self.master, orientation='vertical', border_spacing=0, width=8)
        hbar = AutoScrollbar(self.master, orientation='horizontal', border_spacing=0, height=8)
        vbar.grid(row=0, column=1, padx=(0, 8), pady=(10, 10), sticky='ns')
        hbar.grid(row=1, column=0, padx=(10, 10), pady=(0, 8), sticky='we')

        # Init canvas
        self.canvas = ctk.CTkCanvas(self.master, highlightthickness=0, xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, padx=(10, 10), pady=(10, 10), sticky='nswe')
        self.canvas.update()  # wait until canvas is created

        # Bind scrollbars to the canvas
        vbar.configure(command=self.scroll_y)
        hbar.configure(command=self.scroll_x)

        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.render)  # canvas is changed
        self.canvas.bind('<MouseWheel>', self.wheel)  # zoom

        # Init start fields
        self.base_img = None
        self.img = None  # img to render
        self.width, self.height = None, None
        self.scaled_width, self.scaled_height = None, None
        self.tile = None
        self.scale = 1  # scale is 100%
        self.delta = _zoom_delta  # zoom magnitude
        self.offset = (0, 0)
        self.is_decreased = False  # is decreased
        self.interpolation = Image.Resampling.NEAREST  # interpolation method

    # Set an _img to ImageCanvas
    def set_image(self, _img: Image):
        try:
            if _img is not None:
                self.base_img = _img
                self.img = self.base_img.convert('RGBA')
                self.width, self.height = self.img.size
                self.scaled_width, self.scaled_height = round(self.scale * self.width - 1), round(self.scale * self.height - 1)

                self.tile = (self.width, self.height)
                imagetk = ImageTk.PhotoImage(self.img)
                imageid = self.canvas.create_image((0, 0), anchor='nw', image=imagetk, tag="img")
                self.canvas.tag_lower(imageid)
                self.canvas.imagetk = imagetk
                self.canvas.update()
        except Exception as ex:
            print(ex)

    def __move_from(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def scroll_y(self, *args, **kwargs):
        self.canvas.yview(*args, **kwargs)
        self.render()

    def scroll_x(self, *args, **kwargs):
        self.canvas.xview(*args, **kwargs)
        self.render()

    def wheel(self, event):
        x = self.canvas.canvasx(event.x)     # get cursor position
        y = self.canvas.canvasy(event.y)

        img_box = (0, 0, self.scaled_width, self.scaled_height)  # get img area

        if not (img_box[0] < x < img_box[2] and img_box[1] < y < img_box[3]):  # if cursor position out of the img
            return

        if event.delta == -120:  # scroll down
            if self.scale - self.delta >= 1:
                self.scale -= self.delta
            elif self.scale - self.delta > 0:
                self.scale /= 2

        if event.delta == 120:  # scroll up
            self.scale += self.delta

        if self.scale >= 1:
            self.interpolation = Image.Resampling.NEAREST  # img is increased
        else:
            self.interpolation = Image.Resampling.LANCZOS  # img is decreased

        self.render()

    def render(self, event=None):
        img_box = (0, 0, self.scale * self.width - 1, self.scale * self.height - 1)
        canvas_box = (self.canvas.canvasx(0), self.canvas.canvasy(0), self.canvas.canvasx(self.canvas.winfo_width()), self.canvas.canvasy(self.canvas.winfo_height()))

        self.canvas.configure(scrollregion=[0, 0, self.width * self.scale, self.height * self.scale])

        x1 = max(canvas_box[0] - img_box[0], 0)
        y1 = max(canvas_box[1] - img_box[1], 0)
        x2 = min(canvas_box[2], img_box[2]) - img_box[0]
        y2 = min(canvas_box[3], img_box[3]) - img_box[1]

        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # if visible

            start_point_x = max(int(x1 / self.scale), 0)
            start_point_y = max(int(y1 / self.scale), 0)
            end_point_x = min(math.ceil(x2 / self.scale), self.width) - 1
            end_point_y = min(math.ceil(y2 / self.scale), self.height) - 1

            x_delta = end_point_x - start_point_x + 1
            y_delta = end_point_y - start_point_y + 1

            start_point_x_scaled = x1 % self.scale
            start_point_y_scaled = y1 % self.scale
            end_point_x_scaled = start_point_x_scaled + math.ceil(x2 - x1)
            end_point_y_scaled = start_point_y_scaled + math.ceil(y2 - y1)

            image = self.image.crop((start_point_x, start_point_y, end_point_x + 1, end_point_y + 1))
            image = image.resize((x_delta * self.scale, y_delta * self.scale), Image.Resampling.NEAREST)
            image = image.crop((start_point_x_scaled, start_point_y_scaled, end_point_x_scaled, end_point_y_scaled))

            if self.grid_state and (self.tile is not None):
                self.tile = (int(x1), int(y1), int(x2), int(y2))
                image = self.raster_grid(image, _lines_color=(0, 255, 0, 30))

            imagetk = ImageTk.PhotoImage(image)
            self.offset = max(canvas_box[0], img_box[0]), max(canvas_box[1], img_box[1])
            imageid = self.canvas.create_image(self.offset, anchor='nw', image=imagetk, tag="img")
            self.canvas.tag_lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection


# path = 'C:/Users/User/Dropbox/папка/palace/scripts/opencv/VKR/resources/img_lemons.jpg'  # path to image
# root = ctk.CTk()
#
# img = Image.open(path)
# img_canvas = ImageCanvas(root)
# img_canvas.set_image(img)
#
# root.mainloop()
