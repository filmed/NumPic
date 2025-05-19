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
    settings = {}

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
    settings = {
         "size": {
            "type": "slider",
            "min": 1,
            "max": 250,
            "step": 1,
            "default": 5
        },
        "stabilization": {
            "type": "slider",
            "min": 1,
            "max": 25,
            "step": 1,
            "default": 2
        }
    }

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None
        self.color = "#000000"
        self.size = self.settings["size"]["default"]
        self.stabilization = self.settings["stabilization"]["default"]
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
        width, height = self.renderer.current_layer.img.size
        if (0 <= self.last_x < width) and (0 <= self.last_y < height):
            self.draw_brush(self.last_x, self.last_y)
            self.renderer.composited_img = None
            self.renderer.render()

    def on_drag(self, event):
        if not self.renderer:
            return
        x, y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.current_layer.img.size
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
            self.renderer.composited_img = None
            self.renderer.render()

    def on_release(self, event):
        if not self.renderer:
            return
        x, y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.current_layer.img.size
        if not ((0 <= x < width) and (0 <= y < height)):
            return

        self.connect_points((self.last_x, self.last_y), (x, y))
        self.renderer.composited_img = None
        self.renderer.render()
        self.renderer.layer_manager.layer_rendered()
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
    use_zones = ["editor"]

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None

    def on_use_zone_changed(self, _use_zone):
        if not _use_zone:
            return
        self.renderer = _use_zone

    def on_click(self, event):
        if self.renderer and self.renderer.composited_img:
            x, y = self.canvas2pixel((event.x, event.y))
            width, height = self.renderer.composited_img.size
            if (0 <= x < width) and (0 <= y <= height):
                r, g, b, a = self.renderer.composited_img.getpixel((x, y))
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
            width, height = self.renderer.current_layer.img.size
            if (0 <= x < width) and (0 <= y <= height):
                r, g, b = hex2rgb(self.color)
                print(r, g, b)
                # self.renderer.current_layer.img = flood_fill_cv(self.renderer.current_layer.img, (x, y), (r, g, b, 255))
                # self.renderer.draw = ImageDraw.Draw(self.renderer.current_layer.img)
                flood_fill_cv(self.renderer.current_layer.img, (x, y), (r, g, b, 255))
                self.renderer.composited_img = None
                self.renderer.render()
                self.renderer.layer_manager.layer_rendered()

    def canvas2pixel(self, _pos):
        x = self.renderer.canvas.canvasx(_pos[0])
        y = self.renderer.canvas.canvasy(_pos[1])

        return int(x / self.renderer.scale), int(y / self.renderer.scale)


class EraseTool(BaseTool):
    subscriptions = {"use_zone_changed": "on_use_zone_changed", "size_changed": "on_size_changed"}
    binds = {"<ButtonPress-1>": "on_click", "<B1-Motion>": "on_drag", "<ButtonRelease-1>": "on_release"}
    use_zones = ["editor"]
    settings = {
        "size": {
            "type": "slider",
            "min": 1,
            "max": 250,
            "step": 1,
            "default": 5
        },
        "stabilization": {
            "type": "slider",
            "min": 1,
            "max": 25,
            "step": 1,
            "default": 2
        },
    }

    def __init__(self, _event_bus):
        super().__init__(_event_bus)
        self.renderer = None
        self.color = "#FFFFFF00"
        self.size = self.settings["size"]["default"]
        self.stabilization = self.settings["stabilization"]["default"]
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
        self.renderer.composited_img = None
        self.renderer.render()
        self.renderer.layer_manager.layer_rendered()

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
            self.renderer.composited_img = None
            self.renderer.render()

    def on_release(self, event):
        if not self.renderer:
            return
        self.connect_points((self.last_x, self.last_y), self.canvas2pixel((event.x, event.y)))
        self.renderer.composited_img = None
        self.renderer.render()
        self.renderer.layer_manager.layer_rendered()
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


class CenterChooserTool(BaseTool):
    subscriptions = {
        "use_zone_changed": "on_use_zone_changed",
        "canvas_rendered": "render_pointers",
        "centers_delete_all" : "on_delete_all",
        "center_delete" : "on_delete",
        "center_color_changed" : "on_center_changed"
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
        self.original_dragging_color = None
        self.pointer_radius = 6
        self.pointer_border = 2
        self.isinited = False

    def on_delete_all(self, _data):
        if _data is None:
            return
        self.centers.clear()
        self.clear_pointers()

    def on_delete(self, _color):
        if _color is None:
            return
        if _color in self.centers:
            del self.centers[_color]
            if _color in self.center_widgets:
                self.renderer.canvas.delete(self.center_widgets[_color]["id"])
                del self.center_widgets[_color]

    def on_center_changed(self, _data):
        if not _data:
            return

        old_color, new_color = _data
        if old_color in self.centers:
            self.centers[new_color] = self.centers.pop(old_color)

            if old_color in self.center_widgets:
                widget = self.center_widgets.pop(old_color)
                self.renderer.canvas.delete(widget["id"])

            self.render_pointers()


    def activate(self, **kwargs):
        if not self.isinited:
            self.isinited = True
            self.init_subscribes()
        else:
            self.event_bus.subscribe("use_zone_changed", self.on_use_zone_changed)
            self.event_bus.subscribe("canvas_rendered", self.render_pointers)

        if self.renderer:
            self.render_pointers()

    def deactivate(self):

        self.event_bus.unsubscribe("use_zone_changed", self.on_use_zone_changed)
        self.event_bus.unsubscribe("canvas_rendered", self.render_pointers)
        if self.renderer:
            self.clear_pointers()

    def on_use_zone_changed(self, _use_zone):
        if not _use_zone:
            return
        self.renderer = _use_zone

    def on_click(self, event):
        if not self.renderer or not self.renderer.composited_img:
            return

        x, y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.composited_img.size

        for color, (cx, cy) in self.centers.items():
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy <= self.pointer_radius * self.pointer_radius:
                self.dragging_color = color
                self.original_dragging_color = color
                return

        if (0 <= x < width) and (0 <= y < height):
            r, g, b, a = self.renderer.composited_img.getpixel((x, y))
            self.current_center_color = rgb2hex((r, g, b))

    def on_drag(self, event):
        if not self.dragging_color or not self.renderer:
            return

        x, y = self.canvas2pixel((event.x, event.y))
        width, height = self.renderer.composited_img.size

        if not (0 <= x < width and 0 <= y < height):
            return

        r, g, b, a = self.renderer.composited_img.getpixel((x, y))
        new_color = rgb2hex((r, g, b))

        if new_color != self.dragging_color and (new_color not in self.centers or new_color == self.original_dragging_color):
            old_color = self.dragging_color
            self.centers[new_color] = self.centers.pop(old_color)
            self.dragging_color = new_color

            if old_color in self.center_widgets:
                self.renderer.canvas.delete(self.center_widgets[old_color]["id"])
                del self.center_widgets[old_color]

            self.event_bus.send_state("center_color_change", (old_color, new_color))

        self.centers[self.dragging_color] = (x, y)

        canvas_x = x * self.renderer.scale
        canvas_y = y * self.renderer.scale

        if self.dragging_color in self.center_widgets:
            self.renderer.canvas.coords(
                self.center_widgets[self.dragging_color]["id"],
                canvas_x, canvas_y
            )
        else:
            pointer_img = self.draw_pointer(self.dragging_color)
            img_id = self.renderer.canvas.create_image(
                canvas_x, canvas_y,
                anchor="center",
                image=pointer_img,
                tags=("center_pointer", f"pointer_{self.dragging_color}")
            )
            self.center_widgets[self.dragging_color] = {
                "id": img_id,
                "image": pointer_img
            }

    def on_release(self, event):
        if not self.dragging_color:
            if self.current_center_color and self.current_center_color not in self.centers:
                x, y = self.canvas2pixel((event.x, event.y))
                width, height = self.renderer.composited_img.size

                if (0 <= x < width) and (0 <= y < height):
                    self.centers[self.current_center_color] = (x, y)
                    self.event_bus.send_state("center_add", self.current_center_color)
                    self.render_pointers()

        self.dragging_color = None
        self.original_dragging_color = None
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

    def render_pointers(self, _data=None):
        if not self.renderer:
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

            self.center_widgets[color] = {
                "id": img_id,
                "image": pointer_img
            }


    def clear_pointers(self):
        if self.renderer:
            for widget in self.center_widgets.values():
                self.renderer.canvas.delete(widget["id"])
            self.center_widgets.clear()