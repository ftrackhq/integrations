# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class OutputPlugin(BasePlugin):
    ''' Class representing an Output Plugin
    .. note::

        _required_output a Dictionary '''
    return_type = dict
    plugin_type = constants.PLUGIN_OUTPUT_TYPE
    _required_output = {}

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector or empty list

        *options* a dictionary of options passed from outside.

        Returns self.output Dictionary with the stages and the paths of the collected objects

        .. note::

            Use always self.output as a base to return the values,
            don't override self.output as it contains the _required_output

        .. note::

            Options contains 'component_name' as default option
        '''


        raise NotImplementedError('Missing run method.')