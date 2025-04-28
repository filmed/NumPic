from widgets.custom_button import CustomButton


class ClusterButton(CustomButton):

    def __init__(self, master, _event_bus, _value=None, _is_last=False, **kwargs):
        CustomButton.__init__(self, master, _event_bus, _value, **kwargs)
        if _is_last:
            self.init_subscribes()

    def on_activate(self, **kwargs):
        self.event_bus.send_state("cluster_selected", True)

