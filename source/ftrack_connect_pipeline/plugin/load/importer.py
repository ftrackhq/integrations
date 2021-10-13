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
        #We only want the data of the collector in this stage
        collector_result = []
        component_step = data[-1]
        if component_step.get('category') == 'plugin':
            return method, plugin_settings
        for component_stage in component_step.get("result"):
            if (
                    component_stage.get("name") == constants.COLLECTOR
            ):
                collector_result = component_stage.get("result")
                break
        if collector_result:
            plugin_settings['data'] = collector_result
        return method, plugin_settings

    def get_current_objects(self):
        #TODO: implement this function un the dcc plugin importer.py
        raise NotImplementedError

    def _run(self, event):
        self.old_data = self.get_current_objects()
        self.logger.debug('Current objects : {}'.format(len(self.old_objects)))
        # Having this in a separate method, we can override the parse depending
        #  on the plugin type.
        self._method, self._plugin_settings = self._parse_run_event(event)

        context_data = self.plugin_settings.get('context_data')
        self.logger.debug('Current context : {}'.format(context_data))

        data = self.plugin_settings.get('data')
        self.logger.debug('Current data : {}'.format(data))

        options = self.plugin_settings.get('options')
        self.logger.debug('Current options : {}'.format(options))

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

        asset_load_mode = options.get(asset_const.LOAD_MODE)

        ftrack_asset_class = self.get_asset_class(context_data, data, options)
        ftrack_node = ftrack_asset_class.init_ftrack_object()

        #TODO: if True, the assets willl be load as node
        # only, so the plugin will not be executed but if false the node will be
        # created and the asset will automatically be loaded executing the plugin.
        if not asset_const.LOAD_AS_NODE_ONLY:
            super_result = super(LoaderImporterPlugin, self)._run(event)
            self.new_data = self.get_current_objects()
            self.logger.debug(
                'Scene objects after load : {}'.format(len(self.new_data))
            )

        else:
            #TODO: we can return this or somehow execute the ftracknodes plugin or the ftrack asset class init object.
            super_result = {
                'plugin_name': self.plugin_name,
                'plugin_type': self.plugin_type,
                'method': self.method,
                'status': constants.SUCCESS_STATUS,
                'result': None,
                'execution_time': 0,
                'message': None,
                'user_data': {},#user_data,
                'plugin_id': self.plugin_id
            }


        if asset_load_mode == 'open':
            # TODO:
            #  Don't open the scene after creating the ftrack node, this is wrong,
            #  should be fixed
            #  Open the scene # ERROR, this should go before create the node in this case
            super_result = super(LoaderImporterPlugin, self)._run(event)
            #  Query all the objects from the scene
            self.new_data = self.get_current_objects()
            self.logger.debug(
                'Scene objects after load : {}'.format(len(self.new_data))
            )
            diff = self.new_data.difference(self.old_data)
            #  Connect all the objects that are not dependencies
            ftrack_asset_class.connect_objects(diff)
            #  Check if dependencies already in the scene and what dependencies are missing
            missing_ids, unconected_dependencies, connected_dependencies = ftrack_asset_class.get_missing_dependencies()
            if missing_ids:
                #  if missing dependencies create them
                dependency_objects = self.create_dependency_objects(missing_ids)
                unconected_dependencies.extend(dependency_objects)
            #  connect all the dependencies new and old
            ftrack_asset_class.connect_dependencies(unconected_dependencies)
            # Before save delete only the main ftrackNode
        elif asset_load_mode == 'import':
            # TODO:
            #  IMPORTANT!!! in order to be able to see and choose the way that
            #  we want the dependencies of an import load, we will generate the
            #  asset info for all the dependencies but we will not generate the
            #  node itself as it could be coming in the imported scene. Then when
            #  we import the scene, we check how we have the asset info configured
            #  in order to override the nodes in the imported scene.

            # TODO:
            #  Don't import the scene
            #  Create the ftrack node
            #  Don't create the dependency nodes as we will have them duplicated if we import the asset later on...
            #  When user load the asset with the asset Manager, import, check
            #  dependencies and create the missing ones
            pass
        elif asset_load_mode == 'reference':
            # TODO:
            #  Don't import the scene
            #  Create the ftrack node
            #  Don't create the dependency nodes as we will have them duplicated if we import the asset later on...
            #  When user load the asset with the asset Manager, reference, check
            #  dependencies and Do not create the missing ones
            pass

        #TODO: the _run_plugin method of the engine.init is expecting a return
        # result here. So if we don't execute the plugin we should be returning
        # something anyway.
        return super_result

    def create_dependency_objects(self, missing_dependencies):
        dependency_objects =[]
        for dependency_id in missing_dependencies:
            entity = self.session.query(
                "TypedContext where id is {}".format(dependency_id)
            ).first()
            if not entity:
                continue
            if entity.entity_type == 'Sequence':
                #TODO: think about how to do this one
                # We don't have the assetBuild, task, assetName, the version or the
                # component
                # This one is in case we want to link a sequence inside a project for
                # example.
                pass
            if entity.entity_type == 'Shot' or entity.entity_type == 'AssetBuild':
                dependency_asset_info = asset_info.FtrackAssetInfo.from_asset_build(entity)
                #This should be depending on the DCC
                dependency_asset_info[asset_const.LOAD_MODE] = self.dependency_load_mode
                dependency_object = self.create_ftrack_asset_class(dependency_asset_info)
                dependency_node = dependency_object.init_ftrack_object()
                dependency_objects.append(dependency_object)
        return dependency_objects
