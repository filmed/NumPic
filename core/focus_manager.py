class FocusManager:
    def __init__(self, _root, _event_bus):
        self.root = _root
        self.event_bus = _event_bus
        self.focus_object = None

        self.root.bind_all("<Button-1>", self._on_click_global, add="+")

    def _on_click_global(self, event):
        widget = event.widget

        if widget != self.focus_object:
            self.event_bus.send_state("focus_changed", widget)
            self.focus_object = widget