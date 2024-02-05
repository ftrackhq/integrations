# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


def invoke_in_qt_main_thread(func):
    '''Decorator to ensure the function runs in the QT main thread.'''
    import ftrack_qt.utils.threading

    def wrapper(*args, **kwargs):
        return ftrack_qt.utils.threading.invoke_in_qt_main_thread(
            func, *args, **kwargs
        )

    return wrapper
