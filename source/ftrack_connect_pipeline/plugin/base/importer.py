# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.plugin import BasePlugin, BasePluginValidation
from ftrack_connect_pipeline.constants import plugin
from ftrack_connect_pipeline.asset import asset_info, FtrackAssetBase


class ImporterPluginValidation(BasePluginValidation):
    '''Importer Plugin Validation class'''

    def __init__(self, plugin_name, required_output, return_type, return_value):
        '''Initialise ImporterPluginValidation with *plugin_name*,
        *required_output*, *return_type*, *return_value*.

        *plugin_name* current plugin name stored at the plugin base class

        *required_output* required output of the current plugin stored at
        _required_output of the plugin base class

        *return_type* return type of the current plugin stored at the plugin
        base class

        *return_value* return value of the current plugin stored at the
        plugin base class
        '''
        super(ImporterPluginValidation, self).__init__(
            plugin_name, required_output, return_type, return_value
        )


class BaseImporterPlugin(BasePlugin):
    ''' Class representing an Base Importer Plugin
    .. note::

        _required_output a Dictionary
    '''
    return_type = dict
    plugin_type = plugin._PLUGIN_IMPORTER_TYPE
    asset_node_type = FtrackAssetBase
    _required_output = {}

    def __init__(self, session):
        '''Initialise BaseImporterPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(BaseImporterPlugin, self).__init__(session)
        self.validator = ImporterPluginValidation(
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


    def get_asset_node(self, context, data, options):
        arguments_dict = asset_info.generate_asset_info_dict_from_args(
            context, data, options, self.session
        )

        asset_info_class = asset_info.FtrackAssetInfo(arguments_dict)

        ftrack_node_class = self.asset_node_type(self.event_manager)
        ftrack_node_class.set_asset_info(asset_info_class)
        return ftrack_node_class