# Provides file logic
import os
from customtkinter import filedialog
from PIL import Image
from utils.clust_test import export_all_svgs


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
        if not current_segmented:
            print("Нет сегментированного изображения")
            return

        w, h = current_segmented.size
        _dir = self.current_file_dir or os.path.expanduser("~")
        saving_directory = filedialog.askdirectory(title="Select a directory", initialdir=_dir)

        if saving_directory:
            export_all_svgs(
                contours=current_contours,
                centers=current_centers,
                canvas_size=(w, h),
                save_dir=saving_directory
            )

            png_path = os.path.join(saving_directory, "segmented.png")

            current_segmented.save(png_path)
            print("Сохранено в", saving_directory)






