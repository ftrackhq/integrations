import logging
from ftrack_connect_pipeline.constants.asset import v2, versions_mapping


def generate_asset_info_dict_from_args(context, data, options, session):
    arguments_dict = {}

    arguments_dict[v2.ASSET_NAME] = context.get(
        'asset_name', 'No name found'
    )
    arguments_dict[v2.ASSET_TYPE] = context.get('asset_type', '')
    arguments_dict[v2.ASSET_ID] = context.get('asset_id', '')
    arguments_dict[v2.VERSION_NUMBER] = int(
        context.get('version_number', 0)
    )
    arguments_dict[v2.VERSION_ID] = context.get('version_id', '')
    arguments_dict[v2.CONTEXT_ID] = context.get('context_id', '')

    arguments_dict[v2.ASSET_INFO_OPTIONS] = options.get('load_mode', '')

    asset_version = session.get(
        'AssetVersion', arguments_dict[v2.VERSION_ID]
    )

    location = session.pick_location()

    for component in asset_version['components']:
        if location.get_component_availability(component) < 100.0:
            continue
        component_path = location.get_filesystem_path(component)
        if component_path in data:
            arguments_dict[v2.COMPONENT_NAME] = component['name']
            arguments_dict[v2.COMPONENT_ID] = component['id']
            arguments_dict[v2.COMPONENT_PATH] = component_path

    return arguments_dict



class FtrackAssetInfo(dict):

    @property
    def is_deprecated(self):
        return self._is_deprecated_version

    def __init__(self, mapping, **kwargs):

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._is_deprecated_version = False

        new_mapping = {}
        for k, v in mapping.items():
            if k in versions_mapping.V1_TO_V2_MAPPING.keys():
                self._is_deprecated_version = True
                self.logger.info("Converting deprecated ftrack asset info")
                new_key = versions_mapping.V1_TO_V2_MAPPING[k]
                new_mapping[new_key] = v
            elif k in versions_mapping.V1_TO_V2_MAPPING.values():
                new_mapping[k] = v
        if not new_mapping:
            raise AttributeError(
                "Expecting a diccionary with required asset keys"
            )
        super(FtrackAssetInfo, self).__init__(new_mapping, **kwargs)

