import tkinter as tk
def is_child_of(widget, parent):
    while widget is not None:
        if widget == parent:
            return True
        widget = getattr(widget, "master", None)
    return False

# Tkinter почему-то не предоставляет возможность отвязать от события конкретный обработчик по его id,
# несмотря на то, что документация это подразумевает:
'''If the second argument is a callback bound to that sequence, 
 that callback is removed and the rest, if any, are left in place. 
 If the second argument is omitted, all bindings are deleted.'''
# и требует в качестве второго аргумента для unbind id обработчика, чтобы в итоге удалить все...
# обходной путь для реализации этой логики:
# Author: Juliette Monsel
def unbind(widget, seq, funcid):
    bindings = {x.split()[1][3:]: x for x in widget.bind(seq).splitlines() if x.strip()}
    try:
        del bindings[funcid]
    except KeyError:
        raise tk.TclError('Привязка "%s" не определена.' % funcid)
    widget.bind(seq, '\n'.join(list(bindings.values())))