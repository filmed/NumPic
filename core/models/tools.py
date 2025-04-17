import math
from utils.color_models import rgb2hex, hex2rgb
from utils.figures import fill_intervals, flood_fill_cv
from PIL import ImageDraw


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
        if self.renderer:
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