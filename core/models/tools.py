import math
from utils.color_models import rgb2hex, hex2rgb
from utils.figures import fill_intervals, flood_fill_cv, draw_ellipse
from utils.algs import is_child_of
from PIL import Image, ImageTk, ImageDraw


class BaseTool:

    subscriptions = {}
    binds = {}
    binds_ids = {}
    use_zones = []

    def __init__(self, _event_bus):
        self.event_bus = _event_bus

    def init_subscribes(self):
        for event, callback_name in self.subscriptions.items():
            callback = getattr(self, callback_name)
            self.event_bus.subscribe(event, callback)

    def get_binds(self):
        _result = {}
        for event, callback_name in self.binds.items():
            callback = getattr(self, callback_name)
            _result[event] = callback
        return _result

    def activate(self, **kwargs):
        self.init_subscribes()

    def deactivate(self):
        for event, callback in self.subscriptions.items():
            self.event_bus.unsubscribe(event, callback)


class HandTool(BaseTool):
    subscriptions = {"use_zone_changed": "on_use_zone_changed"}
    binds = {"<ButtonPress-1>": "on_grab", "<B1-Motion>": "on_drag"}
    use_zones = ["editor", "render"]

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None

    def on_use_zone_changed(self, _use_zone):
        if not _use_zone:
            return
        self.renderer = _use_zone

    def on_grab(self, event):
        if self.renderer:
            self.renderer.canvas.scan_mark(event.x, event.y)

    def on_drag(self, event):
        if self.renderer:
            # self.renderer.canvas.configure(cursor="fleur")
            self.renderer.canvas.scan_dragto(event.x, event.y, gain=1)
            self.renderer.render()


class BrushTool(BaseTool):
    subscriptions = {"use_zone_changed": "on_use_zone_changed", "color_changed": "on_color_changed", "size_changed": "on_size_changed"}
    binds = {"<ButtonPress-1>": "on_click", "<B1-Motion>": "on_drag", "<ButtonRelease-1>": "on_release"}
    use_zones = ["editor"]

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None
        self.color = "#000000"
        self.size = 2
        self.stabilization = 2
        self.last_x, self.last_y = None, None
        self.points = []  # Буфер точек для стабилизации

    def on_use_zone_changed(self, _use_zone):
        if not _use_zone:
            return
        self.renderer = _use_zone

    def on_color_changed(self, _color):
        if not _color:
            return
        self.color = _color

    def on_size_changed(self, _size):
        if not _size:
            return
        self.size = _size

    def on_click(self, event):
        if not self.renderer:
            return
        self.last_x, self.last_y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.img.size
        if (0 <= self.last_x < width) and (0 <= self.last_y < height):
            self.draw_brush(self.last_x, self.last_y)
            self.renderer.render()

    def on_drag(self, event):
        if not self.renderer:
            return
        x, y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.img.size
        if not ((0 <= x < width) and (0 <= y < height)):
            return

        self.points.append((x, y))

        if len(self.points) > self.stabilization:
            self.points.pop(0)

        if len(self.points) > 1:
            avg_x = sum(p[0] for p in self.points) // len(self.points)
            avg_y = sum(p[1] for p in self.points) // len(self.points)
            if self.last_x is not None and self.last_y is not None:
                self.connect_points((avg_x, avg_y), (self.last_x, self.last_y))
            self.last_x, self.last_y = avg_x, avg_y
            self.renderer.render()

    def on_release(self, event):
        if not self.renderer:
            return
        x, y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.img.size
        if not ((0 <= x < width) and (0 <= y < height)):
            return

        self.connect_points((self.last_x, self.last_y), (x, y))
        self.renderer.render()
        self.last_x, self.last_y = None, None
        self.points.clear()

    def canvas2pixel(self, _pos):
        x = self.renderer.canvas.canvasx(_pos[0])
        y = self.renderer.canvas.canvasy(_pos[1])

        return int(x / self.renderer.scale), int(y / self.renderer.scale)

    def draw_brush(self, x, y):

        r = int(self.size / 2)

        if r <= 0:
            self.renderer.draw.point((x, y), fill=self.color)
        else:
            self.renderer.draw.ellipse((x - r, y - r, x + r, y + r), fill=self.color)

    def connect_points(self, _point1, _point2):
        (x1, y1), (x2, y2) = _point1, _point2
        steps = int(math.dist((x1, y1), (x2, y2)))
        for i in range(steps):
            t = i / steps
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            self.draw_brush(x, y)


class PipetteTool(BaseTool):
    subscriptions = {"use_zone_changed": "on_use_zone_changed"}
    binds = {"<ButtonPress-1>": "on_click", "<B1-Motion>": "on_click"}
    use_zones = ["editor", "render"]

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None

    def on_use_zone_changed(self, _use_zone):
        if not _use_zone:
            return
        self.renderer = _use_zone

    def on_click(self, event):
        if self.renderer and self.renderer.img:
            x, y = self.canvas2pixel((event.x, event.y))
            width, height = self.renderer.img.size
            if (0 <= x < width) and (0 <= y <= height):
                r, g, b, a = self.renderer.img.getpixel((x, y))
                color = rgb2hex((r, g, b))
                self.event_bus.send_state("color_modify", color)

    def canvas2pixel(self, _pos):
        x = self.renderer.canvas.canvasx(_pos[0])
        y = self.renderer.canvas.canvasy(_pos[1])

        return int(x / self.renderer.scale), int(y / self.renderer.scale)


class FillTool(BaseTool):
    subscriptions = {"use_zone_changed": "on_use_zone_changed", "color_changed": "on_color_changed"}
    binds = {"<ButtonPress-1>": "on_click"}
    use_zones = ["editor"]

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None
        self.color = "#000000"

    def on_use_zone_changed(self, _use_zone):
        if not _use_zone:
            return
        self.renderer = _use_zone

    def on_color_changed(self, _color):
        if not _color:
            return
        self.color = _color

    def on_click(self, event):
        if self.renderer:
            x, y = self.canvas2pixel((event.x, event.y))
            width, height = self.renderer.img.size
            if (0 <= x < width) and (0 <= y <= height):
                r, g, b = hex2rgb(self.color)
                self.renderer.img = flood_fill_cv(self.renderer.img, (x, y), (r, g, b))
                self.renderer.draw = ImageDraw.Draw(self.renderer.img)
                self.renderer.render()

    def canvas2pixel(self, _pos):
        x = self.renderer.canvas.canvasx(_pos[0])
        y = self.renderer.canvas.canvasy(_pos[1])

        return int(x / self.renderer.scale), int(y / self.renderer.scale)


class EraseTool(BaseTool):
    subscriptions = {"use_zone_changed": "on_use_zone_changed", "size_changed": "on_size_changed"}
    binds = {"<ButtonPress-1>": "on_click", "<B1-Motion>": "on_drag", "<ButtonRelease-1>": "on_release"}
    use_zones = ["editor"]

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None
        self.color = "#FFFFFF"
        self.size = 2
        self.stabilization = 2
        self.last_x, self.last_y = None, None
        self.points = []  # Буфер точек для стабилизации

    def on_use_zone_changed(self, _use_zone):
        if not _use_zone:
            return
        self.renderer = _use_zone

    def on_size_changed(self, _size):
        if not _size:
            return
        self.size = _size

    def on_click(self, event):
        if not self.renderer:
            return
        self.last_x, self.last_y = self.canvas2pixel((event.x, event.y))
        self.draw_brush(self.last_x, self.last_y)
        self.renderer.render()

    def on_drag(self, event):
        if not self.renderer:
            return
        self.points.append(self.canvas2pixel((event.x, event.y)))
        if len(self.points) > self.stabilization:
            self.points.pop(0)

        if len(self.points) > 1:
            avg_x = sum(p[0] for p in self.points) // len(self.points)
            avg_y = sum(p[1] for p in self.points) // len(self.points)
            if self.last_x is not None and self.last_y is not None:
                self.connect_points((avg_x, avg_y), (self.last_x, self.last_y))
            self.last_x, self.last_y = avg_x, avg_y
            self.renderer.render()

    def on_release(self, event):
        if not self.renderer:
            return
        self.connect_points((self.last_x, self.last_y), self.canvas2pixel((event.x, event.y)))
        self.renderer.render()
        self.last_x, self.last_y = None, None
        self.points.clear()

    def canvas2pixel(self, _pos):
        x = self.renderer.canvas.canvasx(_pos[0])
        y = self.renderer.canvas.canvasy(_pos[1])

        return int(x / self.renderer.scale), int(y / self.renderer.scale)

    def draw_brush(self, x, y):

        r = int(self.size / 2)

        if r <= 0:
            self.renderer.draw.point((x, y), fill=self.color)
        else:
            self.renderer.draw.ellipse((x - r, y - r, x + r, y + r), fill=self.color)

    def connect_points(self, _point1, _point2):
        (x1, y1), (x2, y2) = _point1, _point2
        steps = int(math.dist((x1, y1), (x2, y2)))
        for i in range(steps):
            t = i / steps
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            self.draw_brush(x, y)



# class CenterChooserTool(BaseTool):
#     subscriptions = {"use_zone_changed": "on_use_zone_changed"}
#     binds = {"<ButtonPress-1>": "change_center", "<B1-Motion>": "change_center", "<ButtonRelease-1>": "add_center"}
#     use_zones = ["editor"]
#
#     def __init__(self, _event_bus):
#         super().__init__(_event_bus)
#         self.renderer = None
#         self.centers = {}
#         self.current_center_color = None
#
#     def on_use_zone_changed(self, _use_zone):
#         if not _use_zone:
#             return
#         self.renderer = _use_zone
#
#     def change_center(self, event):
#         if self.renderer and self.renderer.img:
#             x, y = self.canvas2pixel((event.x, event.y))
#             width, height = self.renderer.img.size
#             if (0 <= x < width) and (0 <= y <= height):
#                 r, g, b, a = self.renderer.img.getpixel((x, y))
#                 self.current_center_color = rgb2hex((r, g, b))
#                 self.event_bus.send_state("color_modify",  self.current_center_color)
#
#     def add_center(self, event):
#         if self.renderer and self.renderer.img:
#             x, y = self.canvas2pixel((event.x, event.y))
#             width, height = self.renderer.img.size
#             if (0 <= x < width) and (0 <= y <= height):
#                 r, g, b, a = self.renderer.img.getpixel((x, y))
#                 self.current_center_color = rgb2hex((r, g, b))
#                 self.event_bus.send_state("color_modify", self.current_center_color)
#
#                 if self.current_center_color not in self.centers:
#                     self.centers[self.current_center_color] = x, y
#                     self.event_bus.send_state("center_added", self.current_center_color)
#
#     def canvas2pixel(self, _pos):
#         x = self.renderer.canvas.canvasx(_pos[0])
#         y = self.renderer.canvas.canvasy(_pos[1])
#
#         return int(x / self.renderer.scale), int(y / self.renderer.scale)
#
#     def draw_pointer(self):
#
#
#     def render_pointers(self):

#
# class CenterChooserTool(BaseTool):
#     subscriptions = {
#         "use_zone_changed": "on_use_zone_changed"
#     }
#     binds = {
#         "<ButtonPress-1>": "on_click",
#         "<B1-Motion>": "on_drag",
#         "<ButtonRelease-1>": "on_release"
#     }
#     use_zones = ["editor"]
#
#     def __init__(self, _event_bus):
#         super().__init__(_event_bus)
#         self.renderer = None
#         self.centers = {}  # color -> (x, y)
#         self.center_widgets = {}  # color -> canvas image ID
#         self.current_center_color = None
#         self.dragging_color = None
#
#         self.pointer_radius = 6
#         self.pointer_border = 2
#
#     def activate(self, **kwargs):
#         self.init_subscribes()
#         if self.renderer:
#             self.render_pointers()
#
#     def deactivate(self):
#         for event, callback in self.subscriptions.items():
#             self.event_bus.unsubscribe(event, callback)
#         if self.renderer:
#             self.clear_pointers()
#
#     def on_use_zone_changed(self, _use_zone):
#         if not _use_zone:
#             return
#         self.renderer = _use_zone
#
#     def on_click(self, event):
#         if not self.renderer or not self.renderer.img:
#             return
#         canvas_x = self.renderer.canvas.canvasx(event.x)
#         canvas_y = self.renderer.canvas.canvasy(event.y)
#
#         # Проверка, не кликнули ли по уже существующему кружку
#         for color, (x, y) in self.centers.items():
#             cx = x * self.renderer.scale
#             cy = y * self.renderer.scale
#             if abs(canvas_x - cx) <= self.pointer_radius and abs(canvas_y - cy) <= self.pointer_radius:
#                 self.dragging_color = color
#                 return
#
#         # Если не по кружку, устанавливаем новый центр
#         x, y = self.canvas2pixel((event.x, event.y))
#         if 0 <= x < self.renderer.img.width and 0 <= y < self.renderer.img.height:
#             r, g, b, a = self.renderer.img.getpixel((x, y))
#             self.current_center_color = rgb2hex((r, g, b))
#             self.event_bus.send_state("color_modify", self.current_center_color)
#
#     def on_drag(self, event):
#         if self.renderer and self.dragging_color:
#             x, y = self.canvas2pixel((event.x, event.y))
#             self.centers[self.dragging_color] = (x, y)
#             self.render_pointers()
#
#     def on_release(self, event):
#         if self.dragging_color:
#             self.event_bus.send_state("center_added", self.dragging_color)
#         self.dragging_color = None
#
#     def canvas2pixel(self, _pos):
#         x = self.renderer.canvas.canvasx(_pos[0])
#         y = self.renderer.canvas.canvasy(_pos[1])
#         return int(x / self.renderer.scale), int(y / self.renderer.scale)
#
#     def draw_pointer(self, color):
#         img_size = self.pointer_radius * 2
#         pointer_img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
#
#         circle = draw_ellipse(
#             pointer_img,
#             [
#                 self.pointer_border,
#                 self.pointer_border,
#                 img_size - self.pointer_border,
#                 img_size - self.pointer_border
#             ],
#             width=self.pointer_border,
#             fillcolor=color,
#             outlinecolor="#ffffffff"
#         )
#         return ImageTk.PhotoImage(circle)
#
#     def render_pointers(self):
#         if not self.renderer:
#             return
#
#         canvas = self.renderer.canvas
#
#         # Удаляем старые
#         self.clear_pointers()
#
#         print("render")
#
#         for color, (x, y) in self.centers.items():
#             px = int(x * self.renderer.scale)
#             py = int(y * self.renderer.scale)
#
#             pointer_img = self.draw_pointer(color)
#             img_id = canvas.create_image(px, py, anchor="center", image=pointer_img)
#             print(f'"id": {img_id}, "image": {pointer_img}')
#             self.center_widgets[color] = {"id": img_id, "image": pointer_img}
#
#     def clear_pointers(self):
#         if self.renderer:
#             canvas = self.renderer.canvas
#             for widget in self.center_widgets.values():
#                 canvas.delete(widget["id"])
#             self.center_widgets.clear()


class CenterChooserTool(BaseTool):
    subscriptions = {
        "use_zone_changed": "on_use_zone_changed",
        "canvas_rendered": "render_pointers"
    }
    binds = {
        "<ButtonPress-1>": "on_click",
        "<B1-Motion>": "on_drag",
        "<ButtonRelease-1>": "on_release"
    }
    use_zones = ["editor"]

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None
        self.centers = {}  # color -> (x, y)
        self.center_widgets = {}  # color -> {"id": canvas_id, "image": PhotoImage}
        self.current_center_color = None
        self.dragging_color = None
        self.pointer_radius = 6
        self.pointer_border = 2

    def activate(self, **kwargs):
        self.init_subscribes()
        if self.renderer:
            self.render_pointers()

    def deactivate(self):
        for event, callback in self.subscriptions.items():
            self.event_bus.unsubscribe(event, callback)
        if self.renderer:
            self.clear_pointers()

    def on_use_zone_changed(self, _use_zone):
        if not _use_zone:
            self.renderer = None
            return
        self.renderer = _use_zone
        self.render_pointers()

    def on_click(self, event):
        if not self.renderer or not self.renderer.img:
            return

        x, y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.img.size

        for color, (cx, cy) in self.centers.items():
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy <= self.pointer_radius * self.pointer_radius:
                self.dragging_color = color
                return

        if (0 <= x < width) and (0 <= y < height):
            r, g, b, a = self.renderer.img.getpixel((x, y))
            self.current_center_color = rgb2hex((r, g, b))
            self.event_bus.send_state("color_modify", self.current_center_color)

    def on_drag(self, event):
        if not self.dragging_color or not self.renderer:
            return

        x, y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.img.size

        if (0 <= x < width) and (0 <= y < height):
            # self.centers[self.dragging_color] = (x, y)
            r, g, b, a = self.renderer.img.getpixel((x, y))
            self.current_center_color = rgb2hex((r, g, b))
            self.event_bus.send_state("color_modify", self.current_center_color)
            pointer_img = self.draw_pointer(self.current_center_color)
            img_id = self.renderer.canvas.create_image(
                x, y,
                anchor="center",
                image=pointer_img,
                tags=("center_pointer", f"pointer_{self.current_center_color}")
            )
            # self.render_pointers()

    def on_release(self, event):
        if not self.dragging_color:
            if self.current_center_color and self.current_center_color not in self.centers:
                x, y = self.canvas2pixel((event.x, event.y))
                width, height = self.renderer.img.size

                if (0 <= x < width) and (0 <= y < height):
                    self.centers[self.current_center_color] = (x, y)
                    self.event_bus.send_state("center_added", self.current_center_color)
                    self.render_pointers()

        self.dragging_color = None
        self.current_center_color = None

    def canvas2pixel(self, pos):
        if not self.renderer:
            return (0, 0)

        x = self.renderer.canvas.canvasx(pos[0])
        y = self.renderer.canvas.canvasy(pos[1])
        return int(x / self.renderer.scale), int(y / self.renderer.scale)

    def draw_pointer(self, color):
        img_size = self.pointer_radius * 2
        pointer_img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))

        circle = draw_ellipse(
            pointer_img,
            [
                self.pointer_border,
                self.pointer_border,
                img_size - self.pointer_border,
                img_size - self.pointer_border
            ],
            width=self.pointer_border,
            fillcolor=color,
            outlinecolor="#ffffffff"
        )
        return ImageTk.PhotoImage(circle)

    def render_pointers(self, _renderer=None):
        if not self.renderer:
            return
        if _renderer:
            if not is_child_of(_renderer, self.renderer):
                return

        self.clear_pointers()

        for color, (x, y) in self.centers.items():
            canvas_x = x * self.renderer.scale
            canvas_y = y * self.renderer.scale

            pointer_img = self.draw_pointer(color)
            img_id = self.renderer.canvas.create_image(
                canvas_x, canvas_y,
                anchor="center",
                image=pointer_img,
                tags=("center_pointer", f"pointer_{color}")
            )

            # Сохраняем ссылки на созданные объекты
            self.center_widgets[color] = {
                "id": img_id,
                "image": pointer_img
            }

    def clear_pointers(self):
        if self.renderer:
            for widget in self.center_widgets.values():
                self.renderer.canvas.delete(widget["id"])
            self.center_widgets.clear()