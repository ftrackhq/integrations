import logging
from ftrack_connect_pipeline.constants import asset as constants


def generate_asset_info_dict_from_args(context, data, options, session):
    '''
    Returns a diccionary constructed from the needed values of the given
    *context*, *data* and *options*

    *context* Context dictionary of the current asset. Should contain the keys
    asset_type, asset_name, asset_id, version_number, version_id, context_id.
    *data* Data of the current operation or plugin. Should contain the
    component_path from the asset that we are working on.
    *options* Options of the current widget or operation, should contain the
    load_mode that we want to/or had apply to the current asset.
    *session* should be the :class:`ftrack_api.session.Session` instance
    to use for communication with the server.
    '''
    arguments_dict = {}

    arguments_dict[constants.ASSET_NAME] = context.get(
        'asset_name', 'No name found'
    )
    arguments_dict[constants.ASSET_TYPE] = context.get('asset_type', '')
    arguments_dict[constants.ASSET_ID] = context.get('asset_id', '')
    arguments_dict[constants.VERSION_NUMBER] = int(
        context.get('version_number', 0)
    )
    arguments_dict[constants.VERSION_ID] = context.get('version_id', '')

    arguments_dict[constants.ASSET_INFO_OPTIONS] = options.get('load_mode', '')

    asset_version = session.get(
        'AssetVersion', arguments_dict[constants.VERSION_ID]
    )

    location = session.pick_location()

    for component in asset_version['components']:
        if location.get_component_availability(component) < 100.0:
            continue
        component_path = location.get_filesystem_path(component)
        if component_path in data:
            arguments_dict[constants.COMPONENT_NAME] = component['name']
            arguments_dict[constants.COMPONENT_ID] = component['id']
            arguments_dict[constants.COMPONENT_PATH] = component_path

    return arguments_dict


class FtrackAssetInfo(dict):
    '''
    Base FtrackAssetInfo class.
    '''

    @property
    def is_deprecated(self):
        '''
        Returns whether the current class is maded up from a legacy mapping type
        of the asset_information.
        '''
        return self._is_deprecated_version

    def _conform_data(self, mapping):
        new_mapping = {}
        for k in constants.KEYS:
            v = mapping.get(k)
            new_mapping.setdefault(k, v)
        return new_mapping

    def __init__(self, mapping=None, **kwargs):
        '''
        Initialize the FtrackAssetInfo with the given *mapping*.

        *mapping* Dictionary with the current asset information.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._is_deprecated_version = False
        mapping = mapping or {}
        mapping = self._conform_data(mapping)
        super(FtrackAssetInfo, self).__init__(mapping, **kwargs)

    def update_asset_version(self, asset_version):
        session = asset_version.session

        asset = asset_version['asset']
        print asset['name']
        self[constants.ASSET_NAME] = asset['name']
        self[constants.ASSET_TYPE] = asset['type']['name']
        self[constants.ASSET_ID] = asset['id']
        self[constants.VERSION_NUMBER] = int(asset_version['version'])
        self[constants.VERSION_ID] = asset_version['id']

        location = session.pick_location()

        for component in asset_version['components']:
            if location.get_component_availability(component) < 100.0:
                continue
            component_path = location.get_filesystem_path(component)
            if component_path:
                self[constants.COMPONENT_NAME] = component['name']
                self[constants.COMPONENT_ID] = component['id']
                self[constants.COMPONENT_PATH] = component_path

        return self
