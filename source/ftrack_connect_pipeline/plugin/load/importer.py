# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import six
import base64

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline.asset import asset_info


class LoaderImporterPlugin(base.BaseImporterPlugin):
    '''
    Base Loader Importer Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseImporterPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_IMPORTER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return output'''

    load_modes = {}
    '''Available load modes for an asset'''

    dependency_load_mode = ''
    '''Default defendency load Mode'''

    def __init__(self, session):
        super(LoaderImporterPlugin, self).__init__(session)

    def _parse_run_event(self, event):
        '''
        Parse the event given on the :meth:`_run`. Returns method name to be
        executed and plugin_setting to be passed to the method.
        This is an override that modifies the plugin_setting['data'] to pass
        only the results of the collector stage of the current step.
        '''
        method, plugin_settings = super(
            LoaderImporterPlugin, self
        )._parse_run_event(event)
        data = plugin_settings.get('data')
        # We only want the data of the collector in this stage
        collector_result = []
        component_step = data[-1]
        if component_step.get('category') == 'plugin':
            return method, plugin_settings
        for component_stage in component_step.get("result"):
            if component_stage.get("name") == constants.COLLECTOR:
                collector_result = component_stage.get("result")
                break
        if collector_result:
            plugin_settings['data'] = collector_result
        return method, plugin_settings

    def get_current_objects(self):
        # TODO: implement this function un the dcc plugin importer.py
        raise NotImplementedError

    def init_nodes(self, context_data=None, data=None, options=None):
        '''Alternative plugin metod to init all the nodes in the scene but not
        need to load the assets'''
        ftrack_object = self.ftrack_asset.init_ftrack_object(False)

        results = [ftrack_object]
        return results

    def _run(self, event):
        self.old_data = self.get_current_objects()
        self.logger.debug('Current objects : {}'.format(len(self.old_data)))
        # Having this in a separate method, we can override the parse depending
        #  on the plugin type.
        self._method, self._plugin_settings = self._parse_run_event(event)

        context_data = self.plugin_settings.get('context_data')
        self.logger.debug('Current context : {}'.format(context_data))

        data = self.plugin_settings.get('data')
        self.logger.debug('Current data : {}'.format(data))

        options = self.plugin_settings.get('options')
        self.logger.debug('Current options : {}'.format(options))

        asset_load_mode = options.get(asset_const.LOAD_MODE)

        # In case of open mode = open or
        # asset_const.LOAD_AS_NODE_ONLY make sure the method is not init_nodes
        if asset_load_mode == 'Open':
            if self.method == 'init_nodes':
                event['data']['pipeline']['method'] = 'run'
                self._method = event['data']['pipeline']['method']

        json_data = json.dumps(event['data'])
        if six.PY2:
            options[asset_const.ASSET_INFO_OPTIONS] = base64.b64encode(
                json_data
            )
        else:
            input_bytes = json_data.encode('utf8')
            options[asset_const.ASSET_INFO_OPTIONS] = base64.b64encode(
                input_bytes
            ).decode('ascii')

        if asset_load_mode != 'Open':
            self.ftrack_asset = self.get_asset_class(
                context_data, data, options
            )

        super_result = super(LoaderImporterPlugin, self)._run(event)

        #  Query all the objects from the scene
        self.new_data = self.get_current_objects()
        self.logger.debug(
            'Scene objects after load : {}'.format(len(self.new_data))
        )
        diff = self.new_data.difference(self.old_data)

        if asset_load_mode != 'Open' and self.method == 'run':
            ftrack_object = self.ftrack_asset.init_ftrack_object(
                is_loaded=True
            )

            #  Connect all the objects that are not dependencies
            self.ftrack_asset.connect_objects(diff)
            #  Check if dependencies already in the scene and what dependencies are missing
            # (
            #    missing_ids,
            #    unconnected_dependencies,
            #    untracked_dependencies,
            # ) = self.ftrack_asset.check_dependencies()
            # if missing_ids:
            #    #  if missing dependencies create them
            #    dependency_objects = self.create_dependency_objects(
            #        missing_ids
            #    )
            #    unconnected_dependencies.extend(dependency_objects)
            # if unconnected_dependencies:
            #    #  connect all the dependencies new and old
            #    self.ftrack_asset.connect_dependencies(
            #        unconnected_dependencies
            #    )
            # Before save delete only the main ftrackNode

        return super_result

    # def create_dependency_objects(self, missing_dependencies):
    #     dependency_objects = []
    #     for dependency_id in missing_dependencies:
    #         entity = self.session.query(
    #             "TypedContext where id is {}".format(dependency_id)
    #         ).first()
    #         if not entity:
    #             continue
    #         if entity.entity_type == 'Sequence':
    #             # TODO: think about how to do this one
    #             # We don't have the assetBuild, task, assetName, the version or the
    #             # component
    #             # This one is in case we want to link a sequence inside a project for
    #             # example.
    #             pass
    #         if (
    #             entity.entity_type == 'Shot'
    #             or entity.entity_type == 'AssetBuild'
    #         ):
    #             dependency_asset_info = (
    #                 asset_info.FtrackAssetInfo.from_context(entity)
    #             )
    #             # This should be depending on the DCC
    #             dependency_asset_info[
    #                 asset_const.LOAD_MODE
    #             ] = self.dependency_load_mode
    #             dependency_asset_info[asset_const.IS_DEPENDENCY] = True
    #             dependency_ftrack_asset = self.create_ftrack_asset_class(
    #                 dependency_asset_info
    #             )
    #             dependency_object = (
    #                 dependency_ftrack_asset.init_ftrack_object()
    #             )
    #             dependency_objects.append(dependency_object)
    #     return dependency_objects
