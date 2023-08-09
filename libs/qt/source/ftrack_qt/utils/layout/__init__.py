# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

def recursive_clear_layout(layout):
    '''Recursively remove all widgets from the *layout*'''
    while layout is not None and layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            recursive_clear_layout(item.layout())