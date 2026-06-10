# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import json
import uuid
import base64

from ftrack_framework_asset_manager.asset import constants


class FtrackAssetInfo(dict):
    def _conform_data(self, mapping):
        new_mapping = {}
        for k in constants.KEYS:
            v = mapping.get(k)
            if v == 'None':
                v = None
            new_mapping.setdefault(k, v)
        return new_mapping

    def __init__(self, mapping=None, **kwargs):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        mapping = mapping or {}
        mapping = self._conform_data(mapping)
        super(FtrackAssetInfo, self).__init__(mapping, **kwargs)

    def encode_options(self, asset_info_options):
        json_data = json.dumps(asset_info_options)
        input_bytes = json_data.encode('utf8')
        return base64.b64encode(input_bytes).decode('ascii')

    def decode_options(self, asset_info_options):
        if not asset_info_options:
            self.logger.error("asset_info_options is empty")
        return json.loads(base64.b64decode(asset_info_options).decode('ascii'))

    def __getitem__(self, k):
        value = super(FtrackAssetInfo, self).__getitem__(k)
        if k == constants.ASSET_INFO_OPTIONS:
            if value:
                value = self.decode_options(value)
        return value

    def __setitem__(self, k, v):
        if k == constants.ASSET_INFO_OPTIONS:
            v = self.encode_options(v)
        super(FtrackAssetInfo, self).__setitem__(k, v)

    def get(self, k, default=None):
        value = super(FtrackAssetInfo, self).get(k, default)
        return value

    def setdefault(self, k, default=None):
        super(FtrackAssetInfo, self).setdefault(k, default)

    @classmethod
    def create(
        cls,
        asset_version_entity,
        component_name,
        component_path=None,
        component_id=None,
        load_mode=None,
        asset_info_options=None,
        objects_loaded=False,
        reference_object=None,
    ):
        asset_entity = asset_version_entity['asset']
        ancestors = asset_entity['ancestors']
        project_name = asset_entity['parent']['project']['name']
        context_path = "{}:{}:{}".format(
            project_name,
            ":".join(x['name'] for x in ancestors),
            asset_entity['name'],
        )

        location = asset_version_entity.session.pick_location()

        if not component_path or not component_id:
            for component in asset_version_entity['components']:
                if component['name'] == component_name:
                    if location.get_component_availability(component) == 100.0:
                        component_path = location.get_filesystem_path(
                            component
                        )
                        if component_path:
                            component_id = component['id']
                            break

        asset_info_data = {
            constants.ASSET_INFO_ID: uuid.uuid4().hex,
            constants.ASSET_NAME: asset_version_entity['asset']['name'],
            constants.ASSET_TYPE_NAME: asset_version_entity['asset']['type'][
                'name'
            ],
            constants.VERSION_ID: asset_version_entity['id'],
            constants.ASSET_ID: asset_version_entity['asset']['id'],
            constants.VERSION_NUMBER: int(asset_version_entity['version']),
            constants.IS_LATEST_VERSION: asset_version_entity[
                constants.IS_LATEST_VERSION
            ],
            constants.DEPENDENCY_IDS: [
                dependency['id']
                for dependency in asset_version_entity['uses_versions']
            ],
            constants.LOAD_MODE: load_mode or 'Not Set',
            constants.ASSET_INFO_OPTIONS: asset_info_options or '',
            constants.OBJECTS_LOADED: objects_loaded,
            constants.REFERENCE_OBJECT: reference_object or '',
            constants.CONTEXT_PATH: context_path,
            constants.COMPONENT_NAME: component_name,
            constants.COMPONENT_ID: component_id,
            constants.COMPONENT_PATH: component_path,
        }

        return cls(asset_info_data)
