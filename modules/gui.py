import cv2
import numpy as np
import keyboard

import tkinter.messagebox
import tkinter as tk
import customtkinter as ctk
from customtkinter import filedialog
from PIL import Image, ImageTk

from ZoomingGrid import Zoom_Advanced
import Pallet

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
        ''' Remember previous coordinates for scrolling with the mouse '''
        CURRENT_USE_ZONE.canvas.scan_mark(event.x, event.y)

    def OnLeftButtonPressedMotion(self, event):
        ''' Drag (move) canvas to the new position '''
        CURRENT_USE_ZONE.canvas.scan_dragto(event.x, event.y, gain=1)
        CURRENT_USE_ZONE.show_image()  # redraw the image

class BrushTool:
    def __init__(self, _icon, _use_zones, _binds):
        self.icon = _icon
        self.use_zones = _use_zones
        self.binds = _binds

    def addBind(self, _bindKey, _bindAction):
        self.binds[_bindKey] = _bindAction

    def OnLeftButtonPress(self, event):
        x = CURRENT_USE_ZONE.canvas.canvasx(event.x)
        y = CURRENT_USE_ZONE.canvas.canvasy(event.y)

        deltax = x - (CURRENT_USE_ZONE.offset[0] - CURRENT_USE_ZONE.tile[0])
        deltay = y - (CURRENT_USE_ZONE.offset[1] - CURRENT_USE_ZONE.tile[1])

        width = CURRENT_USE_ZONE.imscale * CURRENT_USE_ZONE.width
        height = CURRENT_USE_ZONE.imscale * CURRENT_USE_ZONE.height

        if (deltax >= 0) and (deltay >= 0) and ((deltax < width) and (deltay < height)):
            x_pixel = int(deltax // CURRENT_USE_ZONE.imscale)
            y_pixel = int(deltay // CURRENT_USE_ZONE.imscale)

            print(f'{x_pixel}  {y_pixel}')
            #pixel_index = x_pixel + y_pixel * CURRENT_USE_ZONE.width

            # value = APP.radial_pallet.get_pos()
            #
            # APP.img.change_pixel(pixel_index, value)
            # APP.update_image()

    def OnLeftButtonPressedMotion(self, event):
        pass



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
brushtool.addBind('<Motion>', brushtool.OnLeftButtonPressedMotion)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("NumPic")
        self.geometry(f"{1920}x{1080}")

        self.img = None
        self.img_show = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # top bar frame
        self.tb_frame = ctk.CTkFrame(self, corner_radius=0)
        self.tb_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.tbf_label = ctk.CTkLabel(self.tb_frame, text="NumPic", font=ctk.CTkFont(size=16, weight="bold"), text_color="#6b549c")
        self.tbf_label.grid(row=0, column=0, padx=(0, 0), pady=(3, 3), sticky="w")

        self.tbf_loadBtn = ctk.CTkButton(self.tb_frame, command=self.load, corner_radius=3, fg_color="transparent", text="load", text_color="#6b549c")
        self.tbf_loadBtn.grid(row=0, column=1, padx=0, pady=(3, 3), sticky="w")

        self.tbf_saveBtn = ctk.CTkButton(self.tb_frame, command=self.save, corner_radius=3, fg_color="transparent", text="save", text_color="#6b549c")
        self.tbf_saveBtn.grid(row=0, column=2, padx=0, pady=(3, 3), sticky="w")

        # side bar frame
        self.sb_frame = ctk.CTkFrame(self, corner_radius=15, background_corner_colors=['gray86', 'gray92', 'gray92', 'gray86'])
        self.sb_frame.grid(row=1, column=0, sticky="nsw")

        self.sb_frame.grid_columnconfigure((0, 1), weight=1)
        self.sb_frame.grid_rowconfigure((0, 1, 3, 4), weight=1)
        self.sb_frame.grid_rowconfigure((2, 5), weight=0)

        self.sbf_handtoolBtn = ctk.CTkButton(self.sb_frame, text = "Handtool", command= lambda: self.OnToolChanged(handtool), height = 20 , width = 20)
        self.sbf_handtoolBtn.grid(row=0, column=0, padx=(3, 3), pady=(3, 3), sticky="w")

        self.sbf_brushtoolBtn = ctk.CTkButton(self.sb_frame, text = "Brushtool", command= lambda: self.OnToolChanged(brushtool), height = 20 , width = 20)
        self.sbf_brushtoolBtn.grid(row=1, column=0, padx=(3,3), pady=(3, 3), sticky="w")

        #Drawing canvas frame
        self.dcanvas_frame = ctk.CTkFrame(self, corner_radius=6, border_width=3, border_color="#949cb5")
        self.dcanvas_frame.grid(row=1, column=1, padx=(15, 15), pady=(30, 15), sticky="nsew")
        self.dcanvas = None
        # self.dcanvas = Zoom_Advanced(self.dcanvas_frame, self.img_show)
        # self.dcanvas.canvas.bind("<Enter>", lambda event: self.OnChangeUseZone(event, 0))

        # Render canvas frame
        self.rcanvas_frame = ctk.CTkFrame(self, corner_radius=6 , border_width=3, border_color="#949cb5")
        self.rcanvas_frame.grid(row=1, column=2, padx=(15, 15), pady=(30, 15), sticky="nsew")
        self.rcanvas = None
        # self.rcanvas = Zoom_Advanced(self.rcanvas_frame, self.img_show)
        # self.rcanvas.canvas.bind("<Enter>", lambda event: self.OnChangeUseZone(event, 1))

        self.canvases = {0: self.dcanvas, 1: self.rcanvas}

        # create bottomBar frame with widgets
        self.bb_frame = ctk.CTkFrame(self, corner_radius=0)
        self.bb_frame.grid(row=3, column=1,  padx=(15, 15), pady=(15, 15), columnspan=2, sticky="sew")

        self.bb_frame.grid_columnconfigure(0, weight = 1)
        self.bb_frame.grid_columnconfigure(1, weight = 0)

        self.bbf_label = ctk.CTkLabel(self.bb_frame, text="BottomBar", font=ctk.CTkFont(size=16, weight="bold"))
        self.bbf_label.grid(row=0, column=0, padx=(3, 30), pady=(3, 3), sticky="w")

        # create Pallet frame with widgets
        self.pallet_frame = ctk.CTkFrame(self.bb_frame, corner_radius=6 , border_width=3, border_color="#949cb5")
        self.pallet_frame.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), rowspan = 2, sticky="e")

        self.pallet = Pallet.PalletSquare(self.pallet_frame, width = 100, height = 100, indent=-10, spectre_width=20)
        self.pallet.grid(row=0, column=0, padx=(5, 5), pady=(5, 5), sticky="nsew")

        self.current_tool = handtool
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
            self.img = Image.open(self.file_path)
            self.img_show = self.img
            self.dcanvas = Zoom_Advanced(self.dcanvas_frame, self.img_show)
            self.dcanvas.canvas.bind("<Enter>", lambda event: self.OnChangeUseZone(event, 0))
            self.rcanvas = Zoom_Advanced(self.rcanvas_frame, self.img_show)
            self.rcanvas.canvas.bind("<Enter>", lambda event: self.OnChangeUseZone(event, 1))

            #DO SOME STAFF WITH IMG


    def save(self):
        print("save")

        if not self.img is None:
            filetypes = (
                ('text files', '*.txt'),
                ('All files', '*.*')
            )
            self.file_path = filedialog.asksaveasfilename(initialfile='img.png', defaultextension=".png", filetypes=filetypes)
            if self.file_path != "" and self.file_path[-3::] == 'png':
                print(self.file_path)
                self.img_show.save(self.file_path)

    def button_callback(self):
        print("button pressed")

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

    def OnChangeUseZone(self,event, key):
        global CURRENT_USE_ZONE
        CURRENT_USE_ZONE = self.canvases[key]

    def buttons_style(self, _color="#6b549c", _click_color="#5d4987"):
        self.tbf_creteBtn.bind("<Enter>", lambda event: self.tbf_creteBtn.configure(text_color="white", fg_color=_color))
        self.tbf_creteBtn.bind("<Leave>", lambda event: self.tbf_creteBtn.configure(text_color=_color, fg_color="transparent"))
        self.tbf_loadBtn.bind("<Enter>", lambda event: self.tbf_loadBtn.configure(text_color="white", fg_color=_color))
        self.tbf_loadBtn.bind("<Leave>", lambda event: self.tbf_loadBtn.configure(text_color=_color, fg_color="transparent"))

path = 'C:/Users/Nikita/Pictures/Saved Pictures/pokemon.png'  # place path to your image here
# path = 'D:/all/Pictures/misakisa_waifu2x_art_noise2_scale_waifu2x_art_scan_noise2_scale.png'  # place path to your image here

app = App()
app.mainloop()