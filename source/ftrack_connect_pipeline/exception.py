# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


class PipelineError(Exception):
    '''Base pipeline error.'''


class PluginError(PipelineError):
    '''Exception raised in case of plugin error'''