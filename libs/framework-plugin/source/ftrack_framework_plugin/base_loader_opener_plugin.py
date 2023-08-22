# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
import six
import base64

from ftrack_framework_plugin import BasePlugin

# TODO: double check we are allowed to do this, or we should not use constants
#  here, or have host available in base plugin to be able to do something
#  like: host.constants.stage_types.COLLECTOR
import ftrack_constants.framework as constants


# TODO: This is not a base plugin, this should simply be a plugin and should be
# moved to the ftrack_core_plugins. We allways allow list of plugins, so this
# one can be in that list and is not need to use it as base.
# Also review code and test it.
class BaseLoaderOpenerPlugin(BasePlugin):
    '''Base Class to represent a Plugin'''

    # We Define name, plugin_type and host_type as class variables for
    # conviniance for the user when crreating its own plugin.
    name = None
    plugin_type = None
    host_type = None

    @property
    def old_objects(self):
        return self._old_objects

    @property
    def new_objects(self):
        return self._new_objects

    @property
    def all_objects(self):
        return self._all_objects

    @property
    def json_data(self):
        return self._json_data

    def __init__(self, event_manager, host_id, ftrack_object_manager):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(BaseLoaderOpenerPlugin, self).__init__(
            event_manager, host_id, ftrack_object_manager
        )
        self._old_objects = None
        self._new_objects = None
        self._all_objects = None
        self._json_data = None

    # TODO: make this ABC
    def register_methods(self):
        self.register_method(
            method_name='init_nodes',
            required_output_type=dict,
            required_output_value={'asset_info': None, 'dcc_object': None},
        )
        self.register_method(
            method_name='load_asset',
            required_output_type=dict,
            required_output_value={
                'asset_info': None,
                'dcc_object': None,
                'result': None,
            },
        )
        self.register_method(
            method_name='init_and_load',
            required_output_type=dict,
            required_output_value=None,
        )

    # TODO: make this one ABC just for this type
    def collect_current_objects(self):
        raise NotImplementedError

    def init_and_load(self, context_data=None, data=None, options=None):
        '''Alternative plugin method to init and load the node and the assets
        into the scene'''

        init_nodes_result = self.init_nodes(
            context_data=context_data, data=data, options=options
        )
        options['asset_info'] = init_nodes_result.get('asset_info')
        load_asset_result = self.load_asset(
            context_data=context_data, data=data, options=options
        )
        return load_asset_result

    def init_nodes(self, context_data=None, data=None, options=None):
        '''Alternative plugin method to init all the nodes in the scene but not
        need to load the assets'''
        if six.PY2:
            options[constants.asset.ASSET_INFO_OPTIONS] = base64.b64encode(
                self.json_data
            )
        else:
            input_bytes = self.json_data.encode('utf8')
            options[constants.asset.ASSET_INFO_OPTIONS] = base64.b64encode(
                input_bytes
            ).decode('ascii')

        # Get Asset version entity to generate asset info
        asset_version_entity = self.session.query(
            'select version from AssetVersion where id is "{}"'.format(
                context_data[constants.asset.VERSION_ID]
            )
        ).one()

        # Get Component name from collector data.
        component_name = None
        component_path = None
        component_id = None
        for collector in data:
            if not isinstance(collector['result'], dict):
                continue
            else:
                component_name = collector['result'].get(
                    constants.asset.COMPONENT_NAME
                )
                component_path = collector['result'].get(
                    constants.asset.COMPONENT_PATH
                )
                component_id = collector['result'].get(
                    constants.asset.COMPONENT_ID
                )
                break

        self.ftrack_object_manager.create_new_asset_info(
            asset_version_entity,
            component_name=component_name,
            component_path=component_path,
            component_id=component_id,
            load_mode=options.get(constants.asset.LOAD_MODE),
            asset_info_options=options.get(constants.asset.ASSET_INFO_OPTIONS),
        )
        self.ftrack_object_manager.create_new_dcc_object()

        result = {
            'asset_info': self.ftrack_object_manager.asset_info,
            'dcc_object': self.ftrack_object_manager.dcc_object,
        }
        return result

    # TODO: are this ABC for all the importers?
    def load_asset(self, context_data=None, data=None, options=None):
        '''Alternative plugin method to only load the asset in the scene'''

        asset_info = options.get('asset_info')
        self.ftrack_object_manager.asset_info = asset_info
        self.ftrack_object_manager.create_dcc_object_from_asset_info_id(
            asset_info[constants.asset.ASSET_INFO_ID]
        )
        # Remove asset_info from the options as it is not needed anymore
        options.pop('asset_info')

        # Execute the default(usually run) method to load the objects
        execute_fn = getattr(self, self.default_method)
        result = execute_fn(
            context_data=context_data, data=data, options=options
        )

        #  Query all the objects from the scene
        self._all_objects = self.collect_current_objects()
        self.logger.debug(
            'Scene objects after load : {}'.format(len(self.all_objects))
        )
        self._new_objects = self.all_objects.difference(self.old_objects)

        # Set asset_info as loaded.
        self.ftrack_object_manager.objects_loaded = True

        # Connect scene objects to ftrack node
        self.ftrack_object_manager.connect_objects(self._new_objects)

        result = {
            'asset_info': self.ftrack_object_manager.asset_info,
            'dcc_object': self.ftrack_object_manager.dcc_object,
            'result': result,
        }

        return result

    # TODO: This should be ABC
    def pre_execute_callback_hook(self, event):
        if not self.method in ['init_nodes', 'load_asset', 'init_and_load']:
            return event

        # Collect old objects in the scene
        self._old_objects = self.collect_current_objects()

        # TODO: double check if we need this here because seems that in previous code we were not using the context_data, data amd options from the previous
        prevoius_collector_result = self.get_previous_stage_data(
            self.plugin_data, 'collector'
        )

        # set non serializable keys like "session" to not serializable, used in
        # case data contains the asset info from the scene
        self._json_data = json.dumps(
            event['data'], default=lambda o: '<not serializable>'
        )

        return event
