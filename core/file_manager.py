# Provides file logic
import os
from customtkinter import filedialog
from PIL import Image
from utils.clust_test import export_contours_to_svg


class FileManager:
    def __init__(self, _event_bus):
        self.event_bus = _event_bus
        self.valid_types = ["jpg", "jpeg", "png", "bmp"]
        self.file_types = [("Images", "".join(f'*.{valid_type} ' for valid_type in self.valid_types).strip()), ("All files", "*.*")]
        self.current_file_path = None
        self.current_file_dir = None

        self.event_bus.subscribe("file_opening", self.open_file)
        self.event_bus.subscribe("file_saving", self.save_file)

    def open_file(self, _is_opening, _dir=None):
        if not _is_opening:
            return
        _dir = _dir or self.current_file_dir or os.path.expanduser("~")

        file_path = filedialog.askopenfilename(title="Select an image", initialdir=_dir, filetypes=self.file_types)
        if file_path and os.path.isfile(file_path):
            file_type = os.path.splitext(file_path)[1][1:].lower()
            if file_type in self.valid_types:
                self.current_file_path = file_path
                self.current_file_dir = os.path.dirname(file_path)
                image = Image.open(self.current_file_path)
                name = os.path.splitext(os.path.basename(file_path))[0]
                self.event_bus.send_state("file_opened", (image, name))


    def save_file(self, _is_saving):
        if not _is_saving:
            return
        data = self.event_bus.get_state("clusters_changed")
        print("saving: ", data)
        if not data:
            return

        (current_contours, current_centers, current_segmented) = data
        w, h = current_segmented.size
        _dir = self.current_file_dir or os.path.expanduser("~")
        saving_directory = filedialog.askdirectory(title="Select a directory", initialdir=_dir)

        if saving_directory:
            export_contours_to_svg(
                contours=current_contours,
                filename=f"{saving_directory}/contours.svg",
                width=w,
                height=h,
                scale_x=1,
                scale_y=1,
                smooth=False,
                stroke_color="black",
                stroke_width=1,
                stroke_opacity=1.0,
                fill=False
            )
            current_segmented.save(f"{saving_directory}/segmented.png")
            # current_segmented.save(f"{saving_directory}/segmented.svg")
            print(current_centers)




