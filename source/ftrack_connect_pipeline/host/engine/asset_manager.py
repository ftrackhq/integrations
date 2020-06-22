# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import copy
import ftrack_api

from ftrack_connect_pipeline.host.engine import BaseEngine
from ftrack_connect_pipeline import constants


class AssetManagerEngine(BaseEngine):
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host, hostid):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(AssetManagerEngine, self).__init__(
            event_manager, host, hostid, asset_type=None
        )

    def discover_assets(self, data):
        from ftrack_connect_pipeline.asset.asset_info import asset_info_from_ftrack_version
        from ftrack_connect_pipeline_qt.asset.asset_info import QFtrackAsset

        component_name = 'main'
        versions = self.session.query(
            'select id, components, components.name, components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset_id != None and components.name is "{0}" limit 10'.format(
                component_name)
        ).all()

        ftrack_asset_list = []

        for version in versions:
            asset_info = asset_info_from_ftrack_version(version, component_name)
            qasset_info = QFtrackAsset(asset_info, self.event_manager)
            ftrack_asset_list.append(qasset_info)

        return ftrack_asset_list


        # topic = 'topic={}'.format(
        #     constants.PIPELINE_RUN_DISCOVER_ASSETS
        # )
        #
        # event = ftrack_api.event.base.Event(
        #     topic=topic,
        #     data={
        #         'pipeline': {
        #             'host_id': self.hostid,
        #             'data': data
        #         }
        #     }
        # )
        # # TODO: someone has to read this event
        # action_result_data = self.session.event_hub.publish(
        #     event,
        #     synchronous=True
        # )
        #
        # # self._notify_client(action, result_data)
        # return action_result_data
        # # return result_data['status'], result_data['result']

    def change_asset_version(self, data):
        topic = 'topic={}'.format(
            constants.PIPELINE_RUN_CHANGE_ASSET_VERSION
        )

        event = ftrack_api.event.base.Event(
            topic=topic,
            data={
                'pipeline': {
                    'host_id': self.hostid,
                    'data': data
                }
            }
        )
        # TODO: someone has to read this event
        action_result_data = self.session.event_hub.publish(
            event,
            synchronous=True
        )

        # self._notify_client(action, result_data)
        return action_result_data
        # return result_data['status'], result_data['result']












    # #TODO: Not sure to use this one
    # def _notify_client(self, action, result_data):
    #     '''Publish an event to notify client with *data*, plugin_name from
    #     *plugin*, *status* and *message*'''
    #
    #     result_data['hostid'] = self.hostid
    #     #result_data['widget_ref'] = plugin.get('widget_ref')
    #
    #     event = ftrack_api.event.base.Event(
    #         topic=constants.PIPELINE_CLIENT_NOTIFICATION, #Change this topic
    #         data={
    #             'pipeline': result_data
    #         }
    #     )
    #
    #     self.event_manager.publish(
    #         event,
    #     )