import cv2
import numpy as np
import keyboard

import tkinter.messagebox
import tkinter as tk
import customtkinter as ctk
from customtkinter import filedialog
from PIL import Image, ImageTk
from test import ImageCanvas
from Pallet import PalletSquare
import colour
import math


ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


def nothing(*arg):
    pass


class HandTool:
    def __init__(self, _icon, _use_zones, _binds):
        self.icon = _icon
        self.use_zones = _use_zones
        self.binds = _binds

    def addBind(self, _bindKey, _bindAction):
        self.binds[_bindKey] = _bindAction

    def OnLeftButtonPress(self, event):
        CURRENT_USE_ZONE.canvas.scan_mark(event.x, event.y)

    def OnLeftButtonPressedMotion(self, event):
        CURRENT_USE_ZONE.canvas.scan_dragto(event.x, event.y, gain=1)
        CURRENT_USE_ZONE.render()


class BrushTool:
    def __init__(self, _icon, _use_zones, _binds, _size=30, _stabilization=15):
        self.icon = _icon
        self.use_zones = _use_zones
        self.binds = _binds
        self.size = _size
        self.stabilization = _stabilization
        self.color = (0, 0, 0)

        self.last_x, self.last_y = None, None
        self.points = []  # Буфер точек для стабилизации

    def addBind(self, _bindKey, _bindAction):
        self.binds[_bindKey] = _bindAction

    def change_size(self, _size):
        self.size = _size

    def set_color(self, _color):
        self.color = _color

    def canvas2pixel(self, _pos):
        x = CURRENT_USE_ZONE.canvas.canvasx(_pos[0])
        y = CURRENT_USE_ZONE.canvas.canvasy(_pos[1])

        return int(x / CURRENT_USE_ZONE.scale), int(y / CURRENT_USE_ZONE.scale)

    def draw_brush(self, x, y):
        CURRENT_USE_ZONE.draw.ellipse((x - self.size // 2, y - self.size // 2, x + self.size // 2, y + self.size // 2), fill=self.color)

    def connect_points(self, _point1, _point2):
        (x1, y1), (x2, y2) = _point1, _point2
        steps = int(math.dist((x1, y1), (x2, y2)))
        for i in range(steps):
            t = i / steps
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            self.draw_brush(x, y)

    def OnLeftButtonPress(self, event):
        print("left_button pressed!!")
        self.last_x, self.last_y = self.canvas2pixel((event.x, event.y))
        self.draw_brush(self.last_x, self.last_y )
        CURRENT_USE_ZONE.render()

    def OnLeftButtonPressedMotion(self, event):
        self.points.append(self.canvas2pixel((event.x, event.y)))
        if len(self.points) > self.stabilization:
            self.points.pop(0)

        if len(self.points) > 1:
            avg_x = sum(p[0] for p in self.points) // len(self.points)
            avg_y = sum(p[1] for p in self.points) // len(self.points)
            if self.last_x is not None and self.last_y is not None:
                self.connect_points((avg_x, avg_y), (self.last_x, self.last_y))
            self.last_x, self.last_y = avg_x, avg_y
            CURRENT_USE_ZONE.render()

    def OnLeftButtonRelease(self, event):
        self.connect_points((self.last_x, self.last_y),self.canvas2pixel((event.x, event.y)) )
        CURRENT_USE_ZONE.render()
        self.last_x, self.last_y = None, None
        self.points.clear()


class EraserTool:
    def __init__(self, _icon, _use_zones, _binds, _size=30, _stabilization=5):
        self.icon = _icon
        self.use_zones = _use_zones
        self.binds = _binds
        self.size = _size
        self.stabilization = _stabilization
        self.color = "#ffffff"

        self.last_x, self.last_y = None, None
        self.points = []  # Буфер точек для стабилизации

    def addBind(self, _bindKey, _bindAction):
        self.binds[_bindKey] = _bindAction

    def change_size(self, _size):
        self.size = _size

    def canvas2pixel(self, _pos):
        x = CURRENT_USE_ZONE.canvas.canvasx(_pos[0])
        y = CURRENT_USE_ZONE.canvas.canvasy(_pos[1])

        return int(x / CURRENT_USE_ZONE.scale), int(y / CURRENT_USE_ZONE.scale)

    def draw_brush(self, x, y):
        CURRENT_USE_ZONE.draw.ellipse((x - self.size // 2, y - self.size // 2, x + self.size // 2, y + self.size // 2), fill=self.color)

    def connect_points(self, _point1, _point2):
        (x1, y1), (x2, y2) = _point1, _point2
        steps = int(math.dist((x1, y1), (x2, y2)))
        for i in range(steps):
            t = i / steps
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            self.draw_brush(x, y)

    def OnLeftButtonPress(self, event):
        print("left_button pressed!!")
        self.last_x, self.last_y = self.canvas2pixel((event.x, event.y))
        self.draw_brush(self.last_x, self.last_y)
        CURRENT_USE_ZONE.render()

    def OnLeftButtonPressedMotion(self, event):
        self.points.append(self.canvas2pixel((event.x, event.y)))
        if len(self.points) > self.stabilization:
            self.points.pop(0)

        if len(self.points) > 1:
            avg_x = sum(p[0] for p in self.points) // len(self.points)
            avg_y = sum(p[1] for p in self.points) // len(self.points)
            if self.last_x is not None and self.last_y is not None:
                self.connect_points((self.last_x, self.last_y), (avg_x, avg_y))
            self.last_x, self.last_y = avg_x, avg_y
            CURRENT_USE_ZONE.render()

    def OnLeftButtonRelease(self, event):
        self.last_x, self.last_y = None, None
        self.points.clear()



handtool_icon = None
handtool_use_zones = [0, 1]
handtool_binds = {}
handtool = HandTool(handtool_icon, handtool_use_zones, handtool_binds)
handtool.addBind('<ButtonPress-1>', handtool.OnLeftButtonPress)
handtool.addBind('<B1-Motion>', handtool.OnLeftButtonPressedMotion)

brushtool_icon = None
brushtool_use_zones = [0]
brushtool_binds = {}
brushtool = BrushTool(brushtool_icon, brushtool_use_zones, brushtool_binds)
brushtool.addBind('<ButtonPress-1>', brushtool.OnLeftButtonPress)
brushtool.addBind('<B1-Motion>', brushtool.OnLeftButtonPressedMotion)
brushtool.addBind('<ButtonRelease-1>', brushtool.OnLeftButtonRelease)

erasertool_icon = None
erasertool_use_zones = [0]
erasertool_binds = {}
erasertool = EraserTool(erasertool_icon, erasertool_use_zones, erasertool_binds)
erasertool.addBind('<ButtonPress-1>', erasertool.OnLeftButtonPress)
erasertool.addBind('<B1-Motion>', erasertool.OnLeftButtonPressedMotion)
erasertool.addBind('<ButtonRelease-1>', erasertool.OnLeftButtonRelease)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("TestGUI")
        self.geometry(f"{1920}x{1080}")

        self.file = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # top bar frame
        self.tb_frame = ctk.CTkFrame(self, corner_radius=0)
        self.tb_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.tbf_label = ctk.CTkLabel(self.tb_frame, text="TestGUI", font=ctk.CTkFont(size=16, weight="bold"), text_color="#6b549c")
        self.tbf_label.grid(row=0, column=0, padx=(0, 0), pady=(3, 3), sticky="w")

        self.tbf_loadBtn = ctk.CTkButton(self.tb_frame, command=self.load, corner_radius=3, fg_color="transparent", text="load", text_color="#6b549c")
        self.tbf_loadBtn.grid(row=0, column=1, padx=0, pady=(3, 3), sticky="w")

        # side bar frame
        self.sb_frame = ctk.CTkFrame(self, corner_radius=15, background_corner_colors=['gray86', 'gray92', 'gray92', 'gray86'])
        self.sb_frame.grid(row=1, column=0, sticky="nsw")

        self.sb_frame.grid_columnconfigure((0, 1), weight=1)
        self.sb_frame.grid_rowconfigure((0, 1, 3, 4), weight=1)
        self.sb_frame.grid_rowconfigure((2, 5), weight=0)

        self.sbf_handtoolBtn = ctk.CTkButton(self.sb_frame, text = "Handtool", command= lambda: self.OnToolChanged(handtool), height = 20 , width = 20)
        self.sbf_handtoolBtn.grid(row=0, column=0, padx=(3, 3), pady=(3, 3), sticky="w")

        self.sbf_brushtoolBtn = ctk.CTkButton(self.sb_frame, text="Brushtool", command=lambda: self.OnToolChanged(brushtool), height=20, width=20)
        self.sbf_brushtoolBtn.grid(row=1, column=0, padx=(3, 3), pady=(3, 3), sticky="w")

        self.sbf_erasertoolBtn = ctk.CTkButton(self.sb_frame, text="Erasertool", command=lambda: self.OnToolChanged(erasertool), height=20, width=20)
        self.sbf_erasertoolBtn.grid(row=2, column=0, padx=(3, 3), pady=(3, 3), sticky="w")

        #   Create Pallet frame with widgets
        self.sbf_pallet_frame = ctk.CTkFrame(self.sb_frame, corner_radius=6, border_width=3, border_color="#949cb5")
        self.sbf_pallet_frame.grid(row=4, column=0, padx=(0, 0), pady=(0, 0), columnspan=2)

        self.sbf_pallet = PalletSquare(self.sbf_pallet_frame, width=100, height=100, indent=-10, spectre_width=20, _callback=self.color_changed)
        self.sbf_pallet.grid(row=0, column=0, padx=(5, 5), pady=(5, 5), sticky="nsew")
        self.sbf_pallet.bind('<FocusIn>', self.color_changed)

        #   Drawing canvas frame
        self.canvases_frame = ctk.CTkFrame(self, corner_radius=6, border_width=3, border_color="#ff0000")
        self.canvases_frame.grid(row=1, column=1, padx=(5, 5), pady=(5, 5), sticky="nsew")

        self.canvases_frame.grid_rowconfigure(0, weight=1)
        self.canvases_frame.grid_columnconfigure((0, 1), weight=1)

        self.dcanvas_frame = ctk.CTkFrame(self.canvases_frame, corner_radius=6, border_width=3, border_color="#949cb5")
        self.dcanvas_frame.grid(row=0, column=0, padx=(15, 15), pady=(30, 15), sticky="nsew")
        self.dcanvas = ImageCanvas(self.dcanvas_frame)
        self.dcanvas.canvas.bind("<Enter>", lambda event: self.OnChangeUseZone(event, 0))

        # Render canvas frame
        self.rcanvas_frame = ctk.CTkFrame(self.canvases_frame, corner_radius=6 , border_width=3, border_color="#949cb5")
        self.rcanvas_frame.grid(row=0, column=1, padx=(15, 15), pady=(30, 15), sticky="nsew")
        self.rcanvas = ImageCanvas(self.rcanvas_frame)
        self.rcanvas.canvas.bind("<Enter>", lambda event: self.OnChangeUseZone(event, 1))

        self.canvases = {0: self.dcanvas, 1: self.rcanvas}

        self.current_tool = handtool
        self.color_changed()
        self.OnToolChanged(handtool)


    def load(self):
        print("load")

        filetypes = (
            ('Image files', '*.png *.jpg'),
            ('All files', '*.*')
        )
        self.file_path = filedialog.askopenfilename(title='Open a file', initialdir='/', filetypes=filetypes)
        self.tbf_loadBtn.configure(text_color='#6b549c', fg_color="transparent")

        if self.file_path != "":
            print(self.file_path)
            self.file = Image.open(self.file_path)
            self.dcanvas.set_image(self.file)
            self.rcanvas.set_image(self.file)

            #DO SOME STAFF WITH IMG

    def color_changed(self):
        color_hex = self.sbf_pallet.current_color
        color_rgb = colour.hex2rgb(color_hex)
        print(f'color_hex: {color_hex}  color_rgb: {color_rgb}')
        brushtool.set_color(color_hex)

    def OnToolChanged(self, _tool):
        #unbind actions
        for use_zone in self.current_tool.use_zones:
            for bind in self.current_tool.binds:
                self.canvases[use_zone].canvas.bind(bind, nothing)
        self.current_tool = _tool

        #bind new actions
        for use_zone in _tool.use_zones:
            for bind in _tool.binds:
                self.canvases[use_zone].canvas.bind(bind, _tool.binds[bind])

        print(self.current_tool)

    def OnChangeUseZone(self,event, key):
        global CURRENT_USE_ZONE
        CURRENT_USE_ZONE = self.canvases[key]

app = App()
app.mainloop()