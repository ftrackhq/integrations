# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class LoaderPostImporterPlugin(base.BasePostImporterPlugin):
    '''
    Base Loader Post Import Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BasePostImporterPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_POST_IMPORTER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return exporters'''

    def __init__(self, session):
        super(LoaderPostImporterPlugin, self).__init__(session)

    def _parse_run_event(self, event):
        '''
        Parse the event given on the :meth:`_run`. Returns method name to be
        executed and plugin_setting to be passed to the method.
        This is an override that modifies the plugin_setting['data'] to pass
        only the results of the collector stage of the current step.
        '''
        method, plugin_settings = super(
            LoaderPostImporterPlugin, self
        )._parse_run_event(event)
        data = plugin_settings.get('data')
        # We only want the data of the collector in this stage
        collector_result = []
        component_step = data[-1]
        for component_stage in component_step.get("result"):
            if component_stage.get("name") == constants.COLLECTOR:
                collector_result = component_stage.get("result")
                break
        plugin_settings['data'] = collector_result
        return method, plugin_settings
