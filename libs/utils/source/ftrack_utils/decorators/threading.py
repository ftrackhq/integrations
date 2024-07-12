# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


def run_in_main_thread(func):
    def wrapper(self, *args, **kwargs):
        if self.run_in_main_thread_wrapper:
            return self.run_in_main_thread_wrapper(func)(self, *args, **kwargs)
        return func(self, *args, **kwargs)

    return wrapper
