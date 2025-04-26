# Provides file logic
import os
from customtkinter import filedialog
from PIL import Image

class FileManager:
    def __init__(self, _event_bus):
        self.event_bus = _event_bus
        self.valid_types = ["jpg", "jpeg", "png", "bmp"]
        self.file_types = [("Images", "".join(f'*.{valid_type} ' for valid_type in self.valid_types).strip()), ("All files", "*.*")]
        self.current_file = None
        self.current_file_dir = None

        self.event_bus.subscribe("file_selected", self.open_file)
        self.event_bus.subscribe("file_saved", self.save_file)

    def open_file(self, _is_opening, _dir=None):
        if not _is_opening:
            return
        _dir = _dir or self.current_file_dir or os.path.expanduser("~")

        file_path = filedialog.askopenfilename(title="Select an image", initialdir=_dir, filetypes=self.file_types)

        if file_path and os.path.isfile(file_path):
            file_type = os.path.splitext(file_path)[1][1:].lower()
            if file_type in self.valid_types:
                self.current_file = file_path
                self.current_file_dir = os.path.dirname(file_path)
                image = Image.open(self.current_file)
                self.event_bus.send_state("file_opened", image)

    def save_file(self, _file):
        pass


