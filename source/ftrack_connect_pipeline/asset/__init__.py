# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline import constants


class FtrackAssetBase(object):
    '''
        Base FtrackAssetBase class.
    '''

    identity = None
    default_component_name = 'main'

    def is_ftrack_object(self, other):
        raise NotImplementedError()

    @property
    def component_name(self):
        return self.asset_info.get(
            asset_const.COMPONENT_NAME, self.default_component_name
        )

    @property
    def asset_versions(self):
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
        asset_version = self.session.get(
            'AssetVersion', self.asset_info[asset_const.VERSION_ID]
        )
        return asset_version

    @property
    def is_latest(self):
        return self.ftrack_version['is_latest_version']

    @property
    def asset_info(self):
        return self._asset_info

    @asset_info.setter
    def asset_info(self, value):
        if not isinstance(value, FtrackAssetInfo):
            raise ValueError()

        self._asset_info = value

    @property
    def session(self):
        return self.event_manager.session

    @property
    def event_manager(self):
        return self._event_manager

    @property
    def ftrack_object(self):
        return self._ftrack_object

    @ftrack_object.setter
    def ftrack_object(self, value):
        self._ftrack_object = value

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetBase with *ftrack_asset_info*, and *session*.

        *ftrack_asset_info* should be the
        :class:`ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
        instance.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FtrackAssetBase, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._asset_info = None
        self._event_manager = event_manager

        self._ftrack_object = None

    def init_ftrack_object(self):
        '''
        Return the ftrack ftrack_object for this class. It checks if there is
        already a matching ftrack ftrack_object in the scene, in this case it
        updates the ftrack_object if it's not. In case there is no ftrack_object
        in the scene this function creates a new one.
        '''
        self.ftrack_object = None
        return self.ftrack_object

    def _get_unique_ftrack_object_name(self):
        '''
        Return a unique scene name for the current asset_name
        '''
        ftrack_object_name = '{}_ftrackdata'.format(
            self.asset_info[asset_const.ASSET_NAME]
        )
        return ftrack_object_name

    def change_version(self, asset_version_id, host_id):
        '''
        Publish the PIPELINE_ASSET_VERSION_CHANGED event for the given *host_id*
        with the asset info of the given *asset_version_id*.

        note:: Public function to change the asset version, it's been called from
        the api or from the asset manager UI '''

        asset_version = self.session.get('AssetVersion', asset_version_id)

        data_to_send = {'asset_version': asset_version,
                        'component_name': self.component_name}

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_ASSET_VERSION_CHANGED,
            data={
                'pipeline': {
                    'host_id': host_id,
                    'data': data_to_send
                }
            }
        )
        self._event_manager.publish(event, self._change_version)

    def remove_current_objects(self):
        '''
        Remove all the imported or referenced objects in the scene
        '''
        raise NotImplementedError

    def _change_version(self, event):
        '''
        Callback function to change the asset version from the given *event*
        '''

        asset_info = event['data']

        try:
            self.logger.debug("Removing current objects")
            self.remove_current_objects()
        except Exception, e:
            self.logger.error("Error removing current objects: {}".format(e))

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

        return asset_info

    def discover_assets(self):
        '''
        Base discover assets function.
        '''
        ftrack_asset_info_list = []
        return ftrack_asset_info_list

    def clear_selection(self, host_id):
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_ON_CLEAR_SELECTION,
            data={
                'pipeline': {
                    'host_id': host_id,
                    'data': self
                }
            }
        )
        self._event_manager.publish(event, self._clear_selection)

    def _clear_selection(self, event):
        asset_item = event['data']
        return asset_item

    def select_asset(self, host_id):
        '''
        Publish the PIPELINE_ON_SELECT_ASSET event for the given *host_id*
        '''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_ON_SELECT_ASSET,
            data={
                'pipeline': {
                    'host_id': host_id,
                    'data': self
                }
            }
        )
        self._event_manager.publish(event, self._select_asset)

    def _select_asset(self, event):
        asset_item = event['data']
        return asset_item

    def remove_asset(self, host_id):
        '''
        Publish the PIPELINE_ON_REMOVE_ASSET event for the given *host_id*.
        '''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_ON_REMOVE_ASSET,
            data={
                'pipeline': {
                    'host_id': host_id,
                    'data': self
                }
            }
        )
        self._event_manager.publish(event, self._remove_asset)

    def _remove_asset(self, event):
        '''
        Callback function to change the asset version from the given *event*
        '''
        asset_item = event['data']

        return asset_item

