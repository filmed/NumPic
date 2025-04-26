from abc import ABC, abstractmethod


class BaseWidget(ABC):

    subscriptions = {}
    binds = {}

    def __init__(self, _event_bus, _is_last=False):
        self.event_bus = _event_bus
        self.additional_styles = None
        self.event_bus.subscribe("theme_changed", self.apply_theme)
        if _is_last:
            self.init_subscribes()
        self.init_binds()

    def init_subscribes(self):
        for event, callback_name in self.subscriptions.items():
            callback = getattr(self, callback_name)
            self.event_bus.subscribe(event, callback)

    def init_binds(self):
        for event, callback_name in self.binds.items():
            callback = getattr(self, callback_name)
            self.bind(event, callback, add="+")

    def apply_theme(self, _theme):
        if not _theme:
            return

        print(self.__class__.__name__)
        widget_theme = _theme.get(self.__class__.__name__, {})
        try:
            self.additional_styles = widget_theme['additional_styles']
        except:
            pass

        for param, value in widget_theme.items():
            if hasattr(self, "configure") and param != 'additional_styles':
                try:
                    self.configure(**{param: value})
                except Exception as e:
                    print(f"Не удалось применить параметр '{param}': {e}")

    # @abstractmethod
    # def bind(self, _event, _callback):
    #     pass
