# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from functools import partial
import ftrack_api
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline import constants


class FtrackAssetBase(object):
    '''Base FtrackAssetBase class.'''

    identity = None
    default_component_name = 'main'

    def is_ftrack_object(self, object):
        ''' Checks if the given object is '''
        raise NotImplementedError()

    @property
    def component_name(self):
        '''Return component name from the current asset info'''
        return self.asset_info.get(
            asset_const.COMPONENT_NAME, self.default_component_name
        )

    @property
    def ftrack_versions(self):
        '''Returns all the ftrack versions objects of the current asset_id'''
        query = (
            'select is_latest_version, id, asset, components, components.name, '
            'components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}"'
            'order by version ascending'
        ).format(
            self.asset_info[asset_const.ASSET_ID], self.component_name
        )
        versions = self.session.query(query).all()
        return versions

    @property
    def ftrack_version(self):
        '''Returns the ftrack version object of the current version_id'''
        asset_version = self.session.get(
            'AssetVersion', self.asset_info[asset_const.VERSION_ID]
        )
        return asset_version

    @property
    def is_latest(self):
        '''Returns True if the current version is the latest version'''
        return self.ftrack_version['is_latest_version']

    @property
    def asset_info(self):
        '''Returns instance of FtrackAssetInfo'''
        return self._asset_info

    @asset_info.setter
    def asset_info(self, value):
        if not isinstance(value, FtrackAssetInfo):
            raise ValueError()

        self._asset_info = value

    @property
    def session(self):
        '''Returns ftrack session'''
        return self.event_manager.session

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def ftrack_object(self):
        '''Returns ftrack object from the DCC app'''
        return self._ftrack_object

    @ftrack_object.setter
    def ftrack_object(self, value):
        self._ftrack_object = value

    @property
    def definition(self):
        '''Returns ftrack object from the DCC app'''
        return self._definition

    @definition.setter
    def definition(self, value):
        self._definition = value

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetBase with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetBase, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._asset_info = None
        self._event_manager = event_manager

        self._ftrack_object = None
        self._definition = None
        self._ui_event_data = None

    def init_ftrack_object(self):
        '''Returns the ftrack ftrack_object for this class.'''
        self.ftrack_object = None
        return self.ftrack_object

    def _get_unique_ftrack_object_name(self):
        '''Return a unique scene name for the current asset_name'''
        ftrack_object_name = asset_const.FTRACK_OBJECT_NAME.format(
            self.asset_info[asset_const.ASSET_NAME]
        )
        return ftrack_object_name

    def get_plugin(self, plugin_name):
        '''
        Returns the plugin with the given *plugin_name* from the definition
        '''
        for actions_type, plugins in self.definition.get('actions').items():
            for plugin in plugins:
                if str(plugin.get('plugin')) == plugin_name:
                    return plugin

    def change_version(self, asset_version_id, host_connection):
        '''
        Called from the client, runs remove_asset plugin if exists on the host,
        once done call the callback to publish the PIPELINE_ASSET_VERSION_CHANGED
        event to run the change version on the host.
        '''
        schema_engine = self.definition['_config']['engine']
        if not schema_engine:
            return self.logger.error("No engine to run the plugin found")
        remove_plugin = self.get_plugin('remove_asset')
        if not remove_plugin:
            return self.logger.error("No remove_asset plugin found")

        remove_plugin['plugin_data'] = self

        host_connection.run(
            remove_plugin, schema_engine, partial(
                self._publish_change_version_event,
                asset_version_id=asset_version_id,
                host_id=host_connection.id
            )
        )

    def _publish_change_version_event(self, event, asset_version_id, host_id):
        asset_version = self.session.get('AssetVersion', asset_version_id)

        data_to_send = {'asset_version': asset_version,
                        'component_name': self.component_name}

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CHANGE_VERSION,
            data={
                'pipeline': {
                    'host_id': host_id,
                    'data': data_to_send
                }
            }
        )
        self._event_manager.publish(event, self._change_version)

    def _change_version(self, event):
        '''
        Callback function to change the asset version from the given *event*
        '''
        asset_info = event['data']['result']
        host_id = event['data']['host_id']

        asset_info_options = self.asset_info[asset_const.ASSET_INFO_OPTIONS]

        asset_context = asset_info_options['settings']['context']
        asset_data = asset_info[asset_const.COMPONENT_PATH]
        asset_context[asset_const.ASSET_ID] = asset_info[asset_const.ASSET_ID]
        asset_context[asset_const.VERSION_NUMBER] = asset_info[asset_const.VERSION_NUMBER]
        asset_context[asset_const.ASSET_NAME] = asset_info[asset_const.ASSET_NAME]
        asset_context[asset_const.ASSET_TYPE] = asset_info[asset_const.ASSET_TYPE]
        asset_context[asset_const.VERSION_ID] = asset_info[asset_const.VERSION_ID]

        asset_info_options['settings']['data'] = [asset_data]
        asset_info_options['settings']['context'].update(asset_context)

        run_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_RUN_PLUGIN_TOPIC,
            data=asset_info_options
        )
        plugin_result_data = self.session.event_hub.publish(
            run_event,
            synchronous=True
        )
        result_data = plugin_result_data[0]
        if not result_data:
            self.logger.error("Error re-loading asset")

        asset_info[asset_const.ASSET_INFO_OPTIONS] = asset_info_options

        asset_info[asset_const.LOAD_MODE] = self.asset_info[
            asset_const.LOAD_MODE
        ]
        asset_info[asset_const.REFERENCE_OBJECT] = self.asset_info[
            asset_const.REFERENCE_OBJECT
        ]

        if not asset_info:
            self.logger.warning("Asset version couldn't change")
            return
        if not isinstance(asset_info, FtrackAssetInfo):
            raise TypeError(
                "return type of change version has to be type of FtrackAssetInfo"
            )

        self.asset_info.update(asset_info)

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REFRESH_AM,
            data={
                'pipeline': {
                    'host_id': host_id,
                    'data': {},
                }
            }
        )
        self._event_manager.publish(event)

        return asset_info
