import customtkinter as ctk
ctk.set_appearance_mode("light")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.panel = ctk.CTkFrame(self)
        self.panel.grid(row=0, column=0)

        self.renderer = Renderer(self)
        self.renderer.grid(row=0, column=1, sticky="nsew")




class AutoScrollbar(ctk.CTkScrollbar):
    def __init__(self, master, **kwargs):
        ctk.CTkScrollbar.__init__(self, master=master, **kwargs)

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            ctk.CTkScrollbar.set(self, lo, hi)
            self.grid()

class Renderer(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, fg_color="#a0aa00", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Scrollbars
        self.vbar = AutoScrollbar(self, orientation='vertical', border_spacing=0, width=8)
        self.hbar = AutoScrollbar(self, orientation='horizontal', border_spacing=0, height=8)
        self.vbar.grid(row=0, column=1, sticky='ns')
        self.hbar.grid(row=1, column=0, sticky='we')

        # # Outer container with visible mid border
        # self.outline = ctk.CTkFrame(self, fg_color="#ff00ff")
        # self.outline.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")  # ЧЁТНЫЕ паддинги!
        # self.outline.grid_rowconfigure(0, weight=1)
        # self.outline.grid_columnconfigure(0, weight=1)

        # Outer container with visible mid border
        self.canvas_container = ctk.CTkFrame(self, fg_color="#ff00ff")
        self.canvas_container.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")  # ЧЁТНЫЕ паддинги!
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)

        self.canvas = ctk.CTkCanvas(self.canvas_container, bg="white", highlightthickness=0, xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas.configure(highlightthickness=2, highlightbackground="black")

        self.canvas_container.bind("<Configure>", self.adjust_canvas_padding)

    def adjust_canvas_padding(self, event=None):
        width = self.canvas_container.winfo_width()
        height = self.canvas_container.winfo_height()

        mid_border = 3

        if width % 2 == 0:
            pad_left = pad_right = mid_border
        else:
            pad_left = mid_border
            pad_right = mid_border + 1

        if height % 2 == 0:
            pad_top = pad_bottom = mid_border
        else:
            pad_top = mid_border
            pad_bottom = mid_border + 1

        self.canvas.grid_configure(padx=(pad_left, pad_right), pady=(pad_top, pad_bottom))



app = App()
app.mainloop()