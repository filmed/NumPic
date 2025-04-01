import customtkinter as ctk
import re
from PIL import Image, ImageTk,  ImageDraw
import json
from pathlib import Path

root_folder = Path(__file__).parents[1]
themes_path = root_folder / "resources/theme.json"
ctk.set_default_color_theme(themes_path)

# Загружаем JSON-тему
with open(themes_path, "r") as file:
    theme = json.load(file)


def apply_theme(widget, widget_type):
    widget_settings = theme.get(widget_type, {})
    try:
        widget.params = widget_settings['params']
    except:
        pass

    for param, value in widget_settings.items():
        if hasattr(widget, "configure") and param != 'params':
            try:
                widget.configure(**{param: value})
            except Exception as e:
                print(f"Не удалось применить параметр '{param}': {e}")


def hex2rgb(_hex):
    _hex = _hex.replace("#", "")
    return int(_hex[:2], 16), int(_hex[2:4], 16), int(_hex[4:], 16)


def rgb2hex(_rgb):
    return "#" + ''.join(f'{i:02X}' for i in _rgb)


class ColorViewFrame(ctk.CTkFrame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)


class ColorView(ctk.CTkLabel):
    def __init__(self, _master, _color="#ffffff", _color_type="HEX", **kwargs):
        self.master = _master
        super().__init__(self.master, **kwargs)
        apply_theme(self, "ColorView")
        self.types = ["HEX", "RGB"]
        self.color_type = _color_type
        self.color_hex = None
        self.color_rgb = None
        self.text = ""
        self.text_color = None

        self.set_color(_color)

        self.text_color = self.calc_text_color()

    def set_color_type(self, _type):
        if _type in self.types:
            self.color_type = _type
            if self.color_type == "HEX":
                self.text = self.color_hex
            elif self.color_type == "RGB":
                self.text = self.color_rgb
            self.render()

    def set_color(self, _color):
        if _color is not None:
            self.color_hex = _color.upper()
            self.color_rgb = hex2rgb(self.color_hex)

            self.text = self.calc_text()
            self.text_color = self.calc_text_color()
            self.render()

    def calc_text(self):
        if self.color_type == "HEX":
            return self.color_hex
        elif self.color_type == "RGB":
            return self.color_rgb

    def calc_text_color(self):
        L = round(self.color_rgb[0] * 299 / 1000 + self.color_rgb[1] * 587 / 1000 + self.color_rgb[2] * 114 / 1000)
        return "#000000" if L > 128 else "#ffffff"

    def render(self):
        if self.color_hex is not None:
            self.configure(fg_color=self.color_hex, text=self.text, text_color=self.text_color)

class HexColorEntry(ctk.CTkEntry):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.bind("<KeyRelease>", self.validate_hex)

    def validate_hex(self, event=None):
        """Функция валидации HEX цвета и автоматической подстановки решётки."""
        value = self.get()  # Получаем текущий текст

        # Добавляем решётку, если её нет
        if not value.startswith("#"):
            value = "#" + value.lstrip("#")

        # Оставляем только допустимые символы (цифры и буквы a-f)
        value = re.sub(r"[^0-9a-fA-F]", "", value)

        # Ограничиваем длину до 7 символов (включая решётку)
        if len(value) > 7:
            value = value[:7]

        # Обновляем текст в Entry
        self.delete(0, "end")  # Удаляем текущий текст
        self.insert(0, value)  # Вставляем отфильтрованный текст


class CustomRadioButtonFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, _columns=None, _padx=(1, 1), _pady=(1, 1), **kwargs):
        super().__init__(master, **kwargs)
        self.params = None

        apply_theme(self, "CustomRadioButtonFrame")
        self.root = master
        self.pallet_colors = {}

        self.variable = ctk.StringVar(value="")
        self.selected_color = None

        self.padx = _padx
        self.pady = _pady

        self.is_scrollable = True
        self._scrollbar.grid()
        self._scrollbar.configure(height=10)

        self.full_size = (self.params["size"] + self.padx[0] + self.padx[1], self.params["size"] + self.pady[0] + self.pady[1])

        if _columns is not None:
            self.columns = _columns
        else:
            self.columns = self.calc_columns()

        self.rows = self.calc_rows()

        self.grid_columnconfigure(list(range(self.columns)), weight=0)
        self.bind("<Configure>", self.update_frame, add="+")

    def calc_columns(self):
        self.update()
        width = self.winfo_width() if self.winfo_width() > 1 else int(self.cget("width"))
        return max(1, width // self.full_size[0])

    def calc_rows(self):
        count = len(self.pallet_colors)
        return (count + self.columns - 1) // self.columns

    def fill_pallet(self, _pallet):
        for color in _pallet:
            self.add(color)

    def add(self, _color):
        if _color not in self.pallet_colors:
            pallet_element = CustomRadioButton(self, _color=_color, _value=_color, _variable=self.variable)
            self.pallet_colors[_color] = pallet_element
            self.columns = self.calc_columns()
            self.rows = self.calc_rows()
            self.pallet_colors[_color].grid(row=self.rows-1, column=(len(self.pallet_colors) - 1) % self.columns, padx=self.padx, pady=self.pady, sticky="nw")
            self.update_scrollbar()

    def update_frame(self, event=None):
        new_columns = self.calc_columns()
        new_rows = self.calc_rows()

        if new_columns != self.columns or new_rows != self.rows:
            if new_columns != self.columns:
                self.columns = new_columns
                self.grid_columnconfigure(list(range(self.columns)), weight=0)

            for i, key in enumerate(self.pallet_colors):
                self.pallet_colors[key].grid(row=i // self.columns, column=i % self.columns, padx=self.padx, pady=self.pady, sticky="nw")

            if new_rows != self.rows:
                self.rows = new_rows

        self.update_scrollbar()

    def update_scrollbar(self):
        rows = self.calc_rows()
        total_height = rows * self.full_size[1]
        info = self.grid_info()
        row, rowspan, column, columnspan = info["row"], info["rowspan"], info["column"], info["columnspan"]
        bbox = self.root.grid_bbox(column, row, column + columnspan - 1, row + rowspan - 1)
        visible_height = bbox[3]

        if total_height > visible_height and not self.is_scrollable:
            self._scrollbar.grid()
            self.is_scrollable = True
        elif total_height <= visible_height and self.is_scrollable:
            self.is_scrollable = False
            self._scrollbar.grid_remove()

    def get_selected_color(self):
        return self.variable.get() if self.variable else None


class CustomRadioButton(ctk.CTkLabel):
    def __init__(self, master, _color="#ffffff", _value=None, _variable=None, **kwargs):
        super().__init__(master, text="", **kwargs)
        self.params = None
        apply_theme(self, "CustomRadioButton")

        self.value = _value
        self.variable = _variable
        self.color = _color
        self.image_normal = self.button_image(self.params["size"], self.color, self.params["corner_radius"], self.params["border_color_normal"], border_width=self.params["border_width_normal"])
        self.image_selected = self.button_image(self.params["size"], self.color, self.params["corner_radius"], self.params["border_color_selected"], border_width=self.params["border_width_selected"])

        super().__init__(master, image=self.image_normal, text="", **kwargs)
        self.master = master
        self.bind("<Button-1>", self.on_click)

        if self.variable:
            self.variable.trace_add("write", lambda *args: self.update_button())

        self.update_button()

    def button_image(self, size, color, corner_radius, border_color, border_width=3):
        img_size = 2*size
        img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle(
            (0, 0, img_size-1, img_size-1),
            radius=corner_radius,
            fill=color,
            outline=border_color,
            width=border_width
        )
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        return ctk.CTkImage(img, size=(size, size))

    def on_click(self, event=None):
        if self.variable:
            self.variable.set(self.value)
            self.master.selected_color = self.value
            self.update_button()

    def update_button(self):
        if self.variable and self.variable.get() == self.value:
            self.configure(image=self.image_selected)
        else:
            self.configure(image=self.image_normal)


def add():
    color = entry.get().strip()
    pallet_frame.add(f'#{color}')
    color_view.set_color(f'#{color}')

root = ctk.CTk()
root.configure(bg="white")

root.grid_columnconfigure((0, 1), weight=1)
root.grid_rowconfigure((0, 1, 2), weight=1)

entry = HexColorEntry(root, width=150)
entry.grid(row=0, column=0, padx=5, pady=5)

add_button = ctk.CTkButton(root, command=add, corner_radius=3, fg_color="transparent", text="load", text_color="#6b549c")
add_button.grid(row=0, column=1, padx=5, pady=5)

pallet_frame = CustomRadioButtonFrame(root, _padx=(0, 0), _pady=(0, 0))
pallet_frame.grid(row=1, rowspan=2, column=0,  padx=0, pady=0, sticky="nsew")
root.grid_columnconfigure(0, minsize=50, weight=1)
pallet_frame.fill_pallet(["#ff0000", "#00ff00", "#0000ff", "#ff0001", "#00ff02", "#0000f3", "#ff0004", "#00ff05", "#0000f6"])

color_view = ColorView(root, corner_radius=15, font=ctk.CTkFont(size=16, weight="bold"))
color_view.grid(row=1, column=1, padx=0, pady=0, sticky="nsew")
color_view.set_color_type("HEX")
root.mainloop()
