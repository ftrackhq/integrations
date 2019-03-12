

class PipelineError(Exception):
    '''Base pipeline error.'''


class PluginError(PipelineError):
    '''Exception raised in case of plugin error'''