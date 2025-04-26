def is_child_of(widget, parent):
    while widget is not None:
        if widget == parent:
            return True
        widget = getattr(widget, "master", None)
    return False