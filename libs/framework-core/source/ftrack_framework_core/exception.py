# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


# TODO: try to use framework exceptions.
class PipelineError(Exception):
    '''Base pipeline error.'''


class PluginError(PipelineError):
    '''Exception raised in case of plugin error'''


class ValidatorPluginError(PluginError):
    '''Exception raised in case of validator plugin error'''
