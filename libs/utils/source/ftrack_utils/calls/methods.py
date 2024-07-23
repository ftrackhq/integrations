# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


def call_directly(func, *args, **kwargs):
    """
    Directly calls the function passed with given arguments and keyword arguments.

    Parameters:
        func (callable): The function to call.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        The return value of the function called.
    """
    return func(*args, **kwargs)
