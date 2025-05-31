import json
from pathlib import Path
import themes


class ThemeManager:
    def __init__(self, _event_bus):
        self.event_bus = _event_bus
        self.themes = {}
        self.color_vars = {}
        self.current_theme_name = None

        self.init_allowed_themes()
        self.event_bus.subscribe("theme_selected", self.change_theme)

    def init_allowed_themes(self):
        try:
            theme_dir = Path(themes.__file__).parent
            self.themes = {
                json_file.stem: self.preprocess_theme(json.loads(json_file.read_text(encoding='utf-8')))
                for json_file in theme_dir.glob('*.json')
                if json_file.is_file()
            }
        except Exception as e:
            print(f"Theme loading error: {e}")
            self.themes = {'default': {}}

    def change_theme(self, _theme_name):
        if self.current_theme_name != _theme_name:
            if (_theme_name in self.themes) and self.themes[_theme_name]:
                self.current_theme_name = _theme_name
                self.event_bus.send_state("theme_changed", self.themes[self.current_theme_name])

    def get_object_style(self, _object_class_name):
        if self.themes and self.current_theme_name in self.themes:
            return self.themes[self.current_theme_name].get(_object_class_name, {})

    # рекурсивная подстановка цветовых переменных
    def preprocess_theme(self, theme_data):
        self.color_vars = theme_data.pop("_colors", {})
        def replace_colors(obj):
            if isinstance(obj, dict):
                return {k: replace_colors(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_colors(item) for item in obj]
            elif isinstance(obj, str) and obj in self.color_vars:
                return self.color_vars[obj]
            return obj

        return replace_colors(theme_data)
