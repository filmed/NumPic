from core.models.layer import Layer
from core.models import filters
from PIL import Image

class LayerManager:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.layers: list[Layer] = []
        self.current_index = None
        self.background = None

        self.event_bus.subscribe("file_opened", self.init)
        self.event_bus.subscribe("layer_add", self.add)
        self.event_bus.subscribe("layer_delete", self.delete)
        self.event_bus.subscribe("layer_select", self.select)
        self.event_bus.subscribe("layer_move", self.move)
        self.event_bus.subscribe("layer_delete_all", self.delete_all)
        self.event_bus.subscribe("layer_change_name", self.change_name)
        self.event_bus.subscribe("update_filter", self.update_filter_params)



    def init(self, _data):
        if _data is None:
            return
        try:
            print(_data)
            _img, _name = _data
            _size = _img.size
            self.background = Image.new("RGBA", _size, (128, 128, 128, 0))

            _names = self.get_names()
            if _name in _names:
               _name = f"Layer {len(self.layers)}"

            layer = Layer(_name, _img)
            self.layers.append(layer)
            self.current_index = len(self.layers) - 1
            self.event_bus.send_state('layer_inited', layer)
            self.event_bus.send_state('layer_added', layer)


        except Exception as e:
            print(f"layer init ERROR: {e}")


    def add(self, _data=True):
        if _data is None:
            return

        elif _data is True: # empty layer

            _name = f"Layer {len(self.layers)}"

            if self.background is None:
                self.background = Image.new("RGBA", (720, 480), (128, 128, 128, 0))
                self.init((self.background, _name))
                return

            layer = Layer(_name, self.background)
            self.layers.append(layer)
            self.current_index = len(self.layers) - 1
            self.event_bus.send_state('layer_added', layer)


    def delete(self, _data):
        if _data is None:
            return
        if not self.layers:
            return

        if 0 <= self.current_index < len(self.layers):
            _old = self.current_index
            self.layers.pop(self.current_index)
            if self.current_index >= len(self.layers):
                self.current_index = len(self.layers) - 1
            if self.current_index < 0:
                self.current_index = None
            print( (_old, self.current_index))
            self.event_bus.send_state('layer_deleted', (_old, self.current_index))


    def move(self, _data):
        if _data is None:
            return

        if not self.layers:
            return

        target_index = self.current_index - 1 if _data else self.current_index + 1

        if 0 <= target_index < len(self.layers):
            self.layers[self.current_index], self.layers[target_index] = self.layers[target_index], self.layers[self.current_index]
            _old = self.current_index
            self.current_index = target_index
            self.event_bus.send_state('layer_moved', (_old, self.current_index))


    def select(self, _name):
        if _name is None:
            return
        if not self.layers:
            return
        for i, layer in enumerate(self.layers):
            if layer.name == _name:
                self.current_index = i
                self.event_bus.send_state('layer_selected', self.layers[self.current_index])
                break

    def delete_all(self, _data=None):
        if _data is None:
            return
        if not self.layers:
            return

        self.layers.clear()
        self.current_index = None
        self.event_bus.send_state("layer_deleted_all", True)

    def change_name(self, _name=None):
        if _name is None:
            return
        if not self.layers:
            return

        self.layers[self.current_index].name = _name


    def get_current(self):
        if self.current_index is not None and 0 <= self.current_index < len(self.layers):
            return self.layers[self.current_index]
        return None


    def get_merged(self, start=0, end=None, apply_filters=True):
        if end is None:
            end = len(self.layers)

        visible_layers = [layer for layer in self.layers[start:end] if layer.visible and layer.img is not None]

        if not visible_layers:
            return None

        base_size = visible_layers[0].img.size
        result = Image.new("RGBA", base_size, (0, 0, 0, 0))

        if apply_filters:
            for layer in visible_layers:
                img = filters.apply_filters(layer.img, layer.filter_params)
                result.alpha_composite(img)
        else:
            for layer in visible_layers:
                result.alpha_composite(layer.img)

        return result

    def layer_rendered(self):
        if self.layers is None:
            return
        self.event_bus.send_state("layer_rendered", self.current_index)

    def update_filter_params(self, params):
        current = self.get_current()
        if current:
            current.filter_params.update(params)
            self.event_bus.send_state('filter_params_updated', True)

    def get_names(self):
        if self.layers is None:
            return
        result = []
        for layer in self.layers:
            result.append(layer.name)
        return result