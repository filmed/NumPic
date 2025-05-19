import customtkinter as ctk
from PIL import Image
from widgets.base import BaseWidget



class LayerMiniature(BaseWidget, ctk.CTkLabel):
    def __init__(self, master, _event_bus, _img=None, _is_last=False, **kwargs):
        ctk.CTkLabel.__init__(self, master=master, text="", **kwargs)
        BaseWidget.__init__(self, _event_bus=_event_bus)
        self.img = None
        print(self.additional_styles)
        self.size = self.additional_styles.get('size', 30)
        self.set_img(_img)

        if _is_last:
            self.init_subscribes()


    def set_img(self, _img):
        self.img = _img
        self.update_img()

    def update_img(self):
        resized = self.img.resize((self.size, self.size), Image.Resampling.LANCZOS)
        image = ctk.CTkImage(resized, size=(self.size, self.size))
        self.configure(image=image)
        self.update()
