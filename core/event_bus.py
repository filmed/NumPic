#   allows objects to publish events and subscribe to events


class EventBus:
    def __init__(self):
        self.states = {}            # actual data on published events
        self.subscribers = {}       # stores a relationship of type: event -> subscribers

    #   send event to the EventBus and publish them for all subscribers
    def send_state(self, _name, _data=None):
        self.states[_name] = _data
        if _name in self.subscribers:
            for callback in self.subscribers[_name]:
                callback(_data)

    #   get state from the EventBus (not subscribe, just get them once)
    def get_state(self, _name):
        return self.states.get(_name) if _name in self.states else None

    #   subscribe to state changing. Calls _callback on every state changing and immediately after subscription
    def subscribe(self, _name, _callback):
        self.subscribers.setdefault(_name, []).append(_callback)
        #   return actual state after subscribe
        _callback(self.get_state(_name))

    #   remove subscriber of state _name by _callback
    def unsubscribe(self, _name, _callback):
        if _name in self.subscribers:
            if _callback in self.subscribers[_name]:
                self.subscribers[_name].remove(_callback)
