class Layer:
    def __init__(self, _name, _img, _filter_params=None):
        self.name = _name
        self.img = _img.convert('RGBA')
        self.filter_params = _filter_params or {}
        self.visible = True

    def update_filter_params(self, new_params):
        self.filter_params.update(new_params)