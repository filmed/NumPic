import math
import tkinter as tk

import colour
import customtkinter as ctk
import colorsys
from PIL import Image, ImageTk, ImageDraw, ImageOps
import ctypes

# Monitor scale factor
scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100


def hsv2rgb(h,s,v):
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))


def Draw_ellipse(image, bounds, width=3, outlinecolor='white', fillcolor = 'black', antialias=4):

    _image = image.copy()
    mask = Image.new(
        size=[int(dim * antialias) for dim in image.size],
        mode='L', color='black')
    draw = ImageDraw.Draw(mask)

    for offset, fill in (width/-2.0, 'white'), (width/2.0, 'black'):
        left, top = [(value + offset) * antialias for value in bounds[:2]]
        right, bottom = [(value - offset) * antialias for value in bounds[2:]]
        draw.ellipse([left, top, right, bottom], fill=fill)

    mask = mask.resize(image.size, Image.Resampling.LANCZOS)
    # paste outline
    _image.paste(outlinecolor, mask=mask)

    mask = Image.new(
        size=[int(dim * antialias) for dim in image.size],
        mode='L', color='black')
    draw = ImageDraw.Draw(mask)

    for offset, fill in (width / -2.0, 'black'), (width / 2.0, 'white'):
        left, top = [(value + offset) * antialias for value in bounds[:2]]
        right, bottom = [(value - offset) * antialias for value in bounds[2:]]
        draw.ellipse([left, top, right, bottom], fill=fill)

    mask = mask.resize(image.size, Image.Resampling.LANCZOS)
    # paste filling
    _image.paste(fillcolor, mask=mask)

    return _image

class PalletSquare(ctk.CTkFrame):
    def __init__(self, master, width = 150, height = 150, pointer_r = 10, pointer_border = 3, spectre_width = 30, indent = 5, outline = True, outlinecolor = 'red', _callback = None):
        super().__init__(master)

        self.callback = _callback
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # pallet size for show based on monitor DPI scale
        self.outputWidth = int(width * scaleFactor)
        self.outputHeight = int(height * scaleFactor)
        self.outputWidth += self.outputWidth % 2
        self.outputHeight += self.outputHeight % 2

        # pallet size for calculations (not for show function)
        self.palletWidth = 30
        self.palletHeight = round(self.outputHeight / (self.outputWidth / self.palletWidth))
        self.hue_d = 900

        self.pointer_r = pointer_r
        self.pointer_border = pointer_border
        self.pointer_d = 2*self.pointer_r
        self.pointer_moved = False
        self.hpointer_moved = False

        self.spectre_width = spectre_width * scaleFactor
        self.spectre_r = int(math.sqrt(((self.outputWidth + self.pointer_d) ** 2 + (self.outputHeight + self.pointer_d) ** 2) / 4) + indent * scaleFactor + self.pointer_r + self.spectre_width)
        self.canvas_d = int(2 * (self.spectre_r + self.pointer_r))

        self.spectre_xSpacing = ((self.canvas_d - (self.outputWidth + self.pointer_d)) / 2)
        self.spectre_ySpacing = ((self.canvas_d - (self.outputHeight + self.pointer_d)) / 2)

        # Create canvas and put image on it
        self.canvas = ctk.CTkCanvas(self.master, highlightthickness=0, borderwidth=0, width =self.canvas_d, height =self.canvas_d, bg=master.cget("bg_color")[0])
        self.canvas.grid(row=0, column=0, padx=(5, 5), pady=(5, 5))
        self.canvas.update()  # wait till canvas is created

        self.hpointer_x = self.canvas_d / 2 + (self.spectre_r - self.spectre_width / 2) * math.cos(math.radians(0))
        self.hpointer_y = self.canvas_d / 2 + (self.spectre_r - self.spectre_width / 2) * math.sin(math.radians(0))
        self.hue = 0
        self.get_hue()

        self.current_color = colour.rgb2hex(tuple(i for i in colorsys.hsv_to_rgb(self.hue, 1, 1)), force_long=True)

        #self.canvas.bind('<Configure>', self.show_image)     # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.move_from)  # leftButtonPress
        self.canvas.bind('<ButtonRelease-1>', self.stop_move)  # leftButtonPress
        self.canvas.bind('<B1-Motion>', self.move_to)        # leftButtonPressedMoving

        self.pallet = Image.new('RGB', (self.palletWidth, self.palletHeight))  # Create the image
        self.show_image()

        self.spectre = Image.new('RGBA', (self.hue_d, self.hue_d), (0, 0, 0, 0))  # Create empty hue spectre image
        self.create_spectre()
        self.rect = Image.new('RGBA', (self.pointer_d, self.pointer_d), (0, 0, 0, 0))  # Create the image

        self.pointer_x = int(self.canvas_d - (math.ceil(self.spectre_xSpacing) + self.pointer_r))
        self.pointer_y = int((math.ceil(self.spectre_ySpacing) + self.pointer_r))

        self.bbox = self.canvas.bbox(self.imageid)
        self.bbox = (self.bbox[0] - 1, self.bbox[1] - 1, self.bbox[2], self.bbox[3])
        if outline:
            self.container = self.canvas.create_rectangle(self.bbox[0], self.bbox[1],self.bbox[2], self.bbox[3], width = 1, outline=outlinecolor)

        circle = Draw_ellipse(self.rect,[self.pointer_border, self.pointer_border, self.pointer_d - self.pointer_border,self.pointer_d - self.pointer_border], width=self.pointer_border,fillcolor=self.current_color, outlinecolor="#ffffffff")
        self.pointer_img = ImageTk.PhotoImage(image=circle)
        self.my_image = self.canvas.create_image(self.pointer_x, self.pointer_y, image=self.pointer_img)

        circle = Draw_ellipse(self.rect,
                              [self.pointer_border, self.pointer_border, self.pointer_d - self.pointer_border,
                               self.pointer_d - self.pointer_border], width=self.pointer_border,
                              fillcolor=self.current_color, outlinecolor="#ffffffff")
        self.hpointer_img = ImageTk.PhotoImage(image=circle)
        self.my_himage = self.canvas.create_image(self.hpointer_x, self.hpointer_y, image=self.hpointer_img)

    def get_hue(self):
        current_vector = ((self.hpointer_x - self.canvas_d / 2) / self.canvas_d / 2,
                          (self.hpointer_y - self.canvas_d / 2) / self.canvas_d / 2)
        angle1 = math.atan2(0, 1) - math.atan2(current_vector[1], current_vector[0])
        angle1 = angle1 * 360 / (2 * math.pi)
        if (angle1 < 0):
            angle1 = angle1 + 360

        self.hue = angle1 / 360

    def show_image(self, event=None):
        for x in range(self.palletWidth):
            saturation = x / self.palletWidth
            for y in range(self.palletHeight):
                value = 1 - y / self.palletHeight
                self.pallet.putpixel((x, y), tuple(round(i * 255) for i in colorsys.hsv_to_rgb(self.hue, saturation, value)))

        imagetk = ImageTk.PhotoImage(self.pallet.resize((int(self.outputWidth), int(self.outputHeight)), Image.Resampling.BILINEAR))
        self.imageid = self.canvas.create_image(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2,  image=imagetk)
        self.canvas.pallet_image = imagetk  # keep an extra reference to prevent garbage-collection

    def create_spectre(self):
        factor = self.canvas_d / self.hue_d
        for x in range(self.hue_d):
            for y in range(self.hue_d):
                r = math.dist((x,y), (self.hue_d/2, self.hue_d/2))
                if ((self.spectre_r - self.spectre_width) / factor) <= r <= (self.spectre_r / factor):

                    current_vector =((x - self.hue_d/2) /  self.hue_d/2, (y - self.hue_d/2) /self.hue_d/2)

                    angle1 = math.atan2(0, 1) - math.atan2(current_vector[1], current_vector[0])
                    angle1 = angle1 * 180 / math.pi
                    if (angle1 < 0):
                        angle1 = angle1 + 360

                    self.spectre.putpixel((x, y), tuple(round(i * 255) for i in colorsys.hsv_to_rgb(angle1/360, 1, 1)))

        self.spectre =  self.spectre.resize((self.canvas_d, self.canvas_d), Image.Resampling.LANCZOS)
        self.spectre_img = ImageTk.PhotoImage(image=self.spectre)
        my_spectre = self.canvas.create_image(self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2,
                                              image=self.spectre_img)
        self.canvas.lower(my_spectre)  # set image into background
        self.canvas.spectre_image = self.spectre_img  # keep an extra reference to prevent garbage-collection

    def hpointer_changed(self):
        self.get_hue()
        self.get_color()
        self.show_image()

        circle = Draw_ellipse(self.rect,
                              [self.pointer_border, self.pointer_border, self.pointer_d - self.pointer_border,
                               self.pointer_d - self.pointer_border], width=self.pointer_border,
                              fillcolor=self.current_color, outlinecolor="#ffffffff")
        self.pointer_img = ImageTk.PhotoImage(image=circle)
        self.my_image = self.canvas.create_image(self.pointer_x, self.pointer_y, image=self.pointer_img)

        circle = Draw_ellipse(self.rect,
                              [self.pointer_border, self.pointer_border, self.pointer_d - self.pointer_border,
                               self.pointer_d - self.pointer_border], width=self.pointer_border,
                              fillcolor=self.current_color, outlinecolor="#ffffffff")
        self.hpointer_img = ImageTk.PhotoImage(image=circle)
        self.my_himage = self.canvas.create_image(self.hpointer_x, self.hpointer_y, image=self.hpointer_img)

    def move_from(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        r = math.dist((x, y), (self.canvas_d / 2, self.canvas_d / 2))

        if self.bbox[0] < x < self.bbox[2] and self.bbox[1] < y < self.bbox[3]:
            self.pointer_moved = True
            self.pointer_x = x
            self.pointer_y = y
            self.get_color()
            circle = Draw_ellipse(self.rect, [self.pointer_border, self.pointer_border, self.pointer_d - self.pointer_border, self.pointer_d - self.pointer_border], width = self.pointer_border, fillcolor=self.current_color, outlinecolor="#ffffffff")
            self.pointer_img = ImageTk.PhotoImage(image=circle)
            self.my_image = self.canvas.create_image(x, y, image = self.pointer_img)
            self.hpointer_changed()

        elif (self.spectre_r - self.spectre_width) <= r <= self.spectre_r:
            self.hpointer_moved = True
            self.hue_projection(x,y)
            self.hpointer_changed()

    def move_to(self, event):
        if self.pointer_moved == True:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)

            if self.bbox[0] < x < self.bbox[2] and self.bbox[1] < y < self.bbox[3]:
                self.pointer_x = x
                self.pointer_y = y
            else:
                if self.bbox[0] < x < self.bbox[2]:
                    self.pointer_x = x
                else:
                    if x <= self.bbox[0]:
                        self.pointer_x = self.bbox[0] + 1
                    else:
                        self.pointer_x = self.bbox[2]
                if self.bbox[1] < y < self.bbox[3]:
                    self.pointer_y = y
                else:
                    if y <= self.bbox[1]:
                        self.pointer_y = self.bbox[1] + 1
                    else:
                        self.pointer_y = self.bbox[3]

            self.get_color()
            circle = Draw_ellipse(self.rect,[self.pointer_border, self.pointer_border, self.pointer_d - self.pointer_border,self.pointer_d - self.pointer_border], width=self.pointer_border, fillcolor=self.current_color, outlinecolor="#ffffffff")
            self.pointer_img = ImageTk.PhotoImage(image=circle)
            self.my_image = self.canvas.create_image(self.pointer_x, self.pointer_y, image=self.pointer_img)
            self.hpointer_changed()

        elif self.hpointer_moved == True:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)

            self.hue_projection(x, y)
            self.hpointer_changed()

    def hue_projection(self, _x, _y):
        current_vector = ((_x - self.canvas_d / 2) / self.canvas_d / 2, (_y - self.canvas_d / 2) / self.canvas_d / 2)

        angle1 = math.atan2(0, 1) - math.atan2(current_vector[1], current_vector[0])
        angle1 = angle1 * 360 / (2 * math.pi)
        if (angle1 < 0):
            angle1 = angle1 + 360

        angle1 = 360 - angle1

        self.hpointer_x = self.canvas_d / 2 + (self.spectre_r - self.spectre_width / 2) * math.cos(math.radians(angle1))
        self.hpointer_y = self.canvas_d / 2 + (self.spectre_r - self.spectre_width / 2) * math.sin(math.radians(angle1))

    def stop_move(self, event):
        self.pointer_moved = False
        self.hpointer_moved = False

    def get_color(self):
        x = self.pointer_x - (self.pointer_r + self.spectre_xSpacing)
        y = self.pointer_y - (self.pointer_r + self.spectre_ySpacing)

        saturation = x / self.outputWidth
        value = 1 - y / self.outputHeight

        self.current_color = colour.rgb2hex(tuple(i for i in colorsys.hsv_to_rgb(self.hue, saturation, value)), force_long=True)
        if self.callback:
            self.callback()
#
# root = ctk.CTk()
# dcanvas_frame = ctk.CTkFrame(root, corner_radius=6)
# dcanvas_frame.grid(row=0, column=0, padx=(0, 0), pady=(0, 0))
# dcanvas = PalletSquare(dcanvas_frame, width= 200, height = 200,  pointer_r = 10, pointer_border = 5, spectre_width = 15, indent = -10)
# root.mainloop()