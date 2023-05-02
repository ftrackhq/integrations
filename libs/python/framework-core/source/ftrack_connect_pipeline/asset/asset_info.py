# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import json
import uuid
import base64
import six
import os
from ftrack_connect_pipeline.constants import asset as constants


class FtrackAssetInfo(dict):
    '''
    Base FtrackAssetInfo class.
    '''

    def _conform_data(self, mapping):
        '''
        Creates the FtrackAssetInfo object from the given dictionary on the
        *mapping* argument
        '''
        new_mapping = {}
        for k in constants.KEYS:
            v = mapping.get(k)
            # Sometimes the value None is interpreted as unicode (in maya
            # mostly) we are converting to a type None
            if v == u'None':
                v = None
            new_mapping.setdefault(k, v)

        return new_mapping

    def __init__(self, mapping=None, **kwargs):
        '''
        Initialize the FtrackAssetInfo with the given *mapping*.

        *mapping* Dictionary with the asset information.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )
        mapping = mapping or {}
        mapping = self._conform_data(mapping)
        super(FtrackAssetInfo, self).__init__(mapping, **kwargs)

    def encode_options(self, asset_info_options):
        '''
        Encodes the json value from the given *asset_info_opitons*
        to base64.

        *asset_info_opitons* : Options used to load the asset in the scene.
        '''
        json_data = json.dumps(asset_info_options)
        if six.PY2:
            return base64.b64encode(json_data)
        input_bytes = json_data.encode('utf8')
        return base64.b64encode(input_bytes).decode('ascii')

    def decode_options(self, asset_info_options):
        '''
        Decodes the json value from the given *asset_info_opitons*
        from base64.

        *asset_info_opitons* : Options used to load the asset in the scene.
        '''
        if not asset_info_options:
            self.logger.error("asset_info_options is empty")
        if six.PY2:
            return json.loads(base64.b64decode(asset_info_options))
        else:
            return json.loads(
                base64.b64decode(asset_info_options).decode('ascii')
            )

    def __getitem__(self, k):
        '''
        Get the value from the given *k*

        Note:: In case of the given *k* is the asset_info_options it will
        automatically return the decoded json.
        '''

        value = super(FtrackAssetInfo, self).__getitem__(k)
        if k == constants.ASSET_INFO_OPTIONS:
            if value:
                value = self.decode_options(value)
        return value

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k*

        Note:: In case of the given *k* is the asset_info_options it will
        automatically encode the given json value to base64
        '''

        if k == constants.ASSET_INFO_OPTIONS:
            v = self.encode_options(v)
        super(FtrackAssetInfo, self).__setitem__(k, v)

    def get(self, k, default=None):
        '''
        If exists, returns the value of the given *k* otherwise returns
        *default*.

        *k* : Key of the current dictionary.

        *default* : Default value of the given Key.
        '''
        value = super(FtrackAssetInfo, self).get(k, default)
        return value

    def setdefault(self, k, default=None):
        '''
        Sets the *default* value for the given *k*.

        *k* : Key of the current dictionary.

        *default* : Default value of the given Key.
        '''
        super(FtrackAssetInfo, self).setdefault(k, default)

    def _check_asset_info_dependencies(self, value):
        '''
        Return all the dependencies as asset_info. In case the dependency is a
        string convert it to asset_info. (This maya for example)
        '''
        if not value:
            return value
        new_value = []
        for dependency in value:
            if type(dependency) == str:
                dict_dept = dict(eval(dependency))
                dep_asset_info = FtrackAssetInfo(dict_dept)
                new_value.append(dep_asset_info)
                continue
            new_value.append(dependency)
        if new_value:
            value = new_value
        return value

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
        '''
        Returns an :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` object
        generated from the given *asset_version_entity*, and *component_name*.

        *asset_version_entity* : :class:`ftrack_api.entity.asset_version.AssetVersion`

        *component_name* : Component name

        *component_path* : Component path

        *component_id* : Component id

        *load_mode* : Load mode

        *asset_info_options* : Asset info options

        *objects_loaded* : Objects loaded

        *reference_object* : Reference object

        '''

        # Pick context path
        asset_entity = asset_version_entity['asset']
        ancestors = asset_entity['ancestors']
        project_name = asset_entity['parent']['project']['name']
        context_path = "{}:{}:{}".format(
            project_name,
            ":".join(x['name'] for x in ancestors),
            asset_entity['name'],
        )

        # Pick location
        location = asset_version_entity.session.pick_location()

        # Pick component
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
