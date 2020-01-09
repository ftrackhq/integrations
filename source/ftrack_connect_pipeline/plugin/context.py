# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class ContextPlugin(BasePlugin):
    ''' Class representing a Context Plugin
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''
    return_type = dict
    plugin_type = constants.PLUGIN_CONTEXT_TYPE
    _required_output = {'context_id': None, 'asset_name': None,
                        'comment': None, 'status_id': None}

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector or empty list.
        Not used, should be Empty

        *options* a dictionary of options passed from outside.

        Returns self.output a Dictionary with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        .. note::

            Use always self.output as a base to return the values,
            don't override self.output as it contains the _required_output

        '''

        raise NotImplementedError('Missing run method.')
