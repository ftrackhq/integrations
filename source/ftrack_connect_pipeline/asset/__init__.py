# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.constants.asset import v1, v2
import logging


class FtrackAssetInfoV1(dict):
    def __init__(self, context, data, session):
        super(FtrackAssetInfoV1, self).__init__()

        self[v1.ASSET_TYPE] = context.get('asset_type', '')
        self[v1.VERSION_NUMBER] = int(
            context.get('version_number', 0)
        )
        self[v1.VERSION_ID] = context.get('version_id', '')

        asset_version = session.get(
            'AssetVersion', self[v1.VERSION_ID]
        )

        location = session.pick_location()

        for component in asset_version['components']:
            if location.get_component_availability(component) < 100.0:
                continue
            component_path = location.get_filesystem_path(component)
            if component_path in data:
                self[v1.COMPONENT_NAME] = component['name']
                self[v1.COMPONENT_ID] = component['id']
                self[v1.COMPONENT_PATH] = component_path


class FtrackAssetInfoV2(dict):
    def __init__(self, context, data, session):
        super(FtrackAssetInfoV2, self).__init__()

        self[v2.ASSET_NAME] = context.get(
            'asset_name', 'No name found'
        )
        self[v2.ASSET_TYPE] = context.get('asset_type', '')
        self[v2.ASSET_ID] = context.get('asset_id', '')
        self[v2.VERSION_NUMBER] = int(
            context.get('version_number', 0)
        )
        self[v2.VERSION_ID] = context.get('version_id', '')
        self[v2.CONTEXT_ID] = context.get('context_id', '')

        asset_version = session.get(
            'AssetVersion', self[v2.VERSION_ID]
        )

        location = session.pick_location()

        for component in asset_version['components']:
            if location.get_component_availability(component) < 100.0:
                continue
            component_path = location.get_filesystem_path(component)
            if component_path in data:
                self[v2.COMPONENT_NAME] = component['name']
                self[v2.COMPONENT_ID] = component['id']
                self[v2.COMPONENT_PATH] = component_path


class FtrackAssetInfo(dict):
    '''
    Dictionary class containing ftrack asset information from the given context
    '''
    def __init__(self, context, data, session):
        '''
        Initialize FtrackAssetInfo with the give *context*, *data* and *session*.

        *context* Dicctionary with asset_name, asset_type, asset_id,
        version_number, version_id, context_id keys and values from the current
        asset.
        *data* List of component paths of the current asset.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FtrackAssetInfo, self).__init__()
        self.update(FtrackAssetInfoV1(context, data, session))
        self.update(FtrackAssetInfoV2(context, data, session))


class FtrackAssetBase(object):
    '''
        Base FtrackAssetNode class.
    '''
    def __init__(self, context, data, session):
        '''
            Initialize FtrackAssetNode with *asset_info*, and optional
            *asset_import_mode*.

            *asset_info* Dictionary with the current asset information from
            ftrack. Needed keys: asset_name, version_number, context_id,
            asset_type, asset_id, version_id, component_name, component_id,
            compoennt_path.
        '''
        super(FtrackAssetBase, self).__init__()

        self.logger = logging.getLogger(__name__)

        self.context = context
        self.data = data
        self.session = session

        self.asset_info = FtrackAssetInfo(self.context, self.data, self.session)
