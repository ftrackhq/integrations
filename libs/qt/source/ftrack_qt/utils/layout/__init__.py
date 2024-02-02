# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


def recursive_clear_layout(layout, removed_widgets=[]):
    '''Recursively remove all widgets from the *layout*'''
    for i in reversed(range(layout.count())):
        item = layout.takeAt(i)
        widget = item.widget()
        if widget is not None:
            if hasattr(widget, 'widget'):
                if (
                    hasattr(widget.widget(), 'layout')
                    and widget.widget().layout()
                ):
                    recursive_clear_layout(
                        widget.widget().layout(), removed_widgets
                    )
            elif hasattr(widget, 'layout') and widget.layout():
                recursive_clear_layout(widget.layout(), removed_widgets)
            removed_widgets.append(widget)
            widget.deleteLater()
        else:
            if hasattr(item, 'layout') and item.layout():
                recursive_clear_layout(item.layout(), removed_widgets)
