# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.plugin import BasePlugin, BasePluginValidation
from ftrack_connect_pipeline.constants import plugin
from ftrack_connect_pipeline.asset import asset_info as ainfo
from ftrack_connect_pipeline.asset import FtrackAssetBase


class ImporterPluginValidation(BasePluginValidation):
    '''
    Importer Plugin Validation class inherits from
    :class:`~ftrack_connect_pipeline.plugin.BasePluginValidation`
    '''

    def __init__(
        self, plugin_name, required_output, return_type, return_value
    ):
        super(ImporterPluginValidation, self).__init__(
            plugin_name, required_output, return_type, return_value
        )


class BaseImporterPlugin(BasePlugin):
    '''
    Base Importer Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.BasePlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = plugin._PLUGIN_IMPORTER_TYPE
    '''Type of the plugin'''
    ftrack_asset_class = FtrackAssetBase
    '''Define the class to use for the ftrack node to track the loaded assets'''
    _required_output = {}
    '''Required return output'''

    def __init__(self, session):
        super(BaseImporterPlugin, self).__init__(session)
        self.validator = ImporterPluginValidation(
            self.plugin_name,
            self._required_output,
            self.return_type,
            self.return_value,
        )

    def run(self, context_data=None, data=None, options=None):
        raise NotImplementedError('Missing run method.')

    def generate_asset_info_from_plugin_arguments(self, context_data, data, options):
        '''
        Returns :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
        created by the
        :meth:`~ftrack_connect_pipeline.asset.asset_info.generate_asset_info_dict_from_args`
        method using the given *context_data*, *data*, and *options*.
        '''
        arguments_dict = ainfo.generate_asset_info_dict_from_args(
            context_data, data, options, self.session
        )

        asset_info = ainfo.FtrackAssetInfo(arguments_dict)

        return asset_info
