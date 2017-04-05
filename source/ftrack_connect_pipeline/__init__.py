# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack


from ._version import __version__


_plugin = None


def register_plugin(new_plugin):
    '''Register *new_plugin*.'''
    global _plugin

    if _plugin is not None:
        raise ValueError('Plugin {0!r} already registered'.format(_plugin))

    _plugin = new_plugin


def get_plugin():
    '''Return plugin.'''
    global _plugin

    if _plugin is None:
        raise ValueError('No plugin registered.')

    return _plugin
