# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.plugin import BasePlugin, BasePluginValidation
from ftrack_connect_pipeline.constants import plugin


class OutputPluginValidation(BasePluginValidation):
    '''Output Plugin Validation class'''

    def __init__(self, plugin_name, required_output, return_type, return_value):
        '''Initialise OutputPluginValidation with *plugin_name*,
        *required_output*, *return_type*, *return_value*.

        *plugin_name* current plugin name stored at the plugin base class

        *required_output* required output of the current plugin stored at
        _required_output of the plugin base class

        *return_type* return type of the current plugin stored at the plugin
        base class

        *return_value* return value of the current plugin stored at the
        plugin base class
        '''
        super(OutputPluginValidation, self).__init__(
            plugin_name, required_output, return_type, return_value
        )


class BaseOutputPlugin(BasePlugin):
    ''' Class representing an Output Plugin
    .. note::

        _required_output a Dictionary
    '''
    return_type = dict
    plugin_type = plugin._PLUGIN_OUTPUT_TYPE
    _required_output = {}

    def __init__(self, session):
        '''Initialise OutputPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(BaseOutputPlugin, self).__init__(session)
        self.validator = OutputPluginValidation(
            self.plugin_name, self._required_output, self.return_type,
            self.return_value
        )

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id,
        asset_type, comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector or empty list

        *options* a dictionary of options passed from outside.

        Returns self.output Dictionary with the stages and the paths of the
        collected objects

        .. note::

            Use always self.output as a base to return the values,
            don't override self.output as it contains the _required_output

        .. note::

            Options contains 'component_name' as default option
        '''


        raise NotImplementedError('Missing run method.')