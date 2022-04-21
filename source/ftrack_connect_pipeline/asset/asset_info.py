# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import json
import uuid
import base64
import six
import ftrack_api
from ftrack_connect_pipeline.constants import asset as constants


def generate_asset_info_dict_from_args(context_data, data, options, session):
    '''
    Returns a dictionary constructed from the needed values of the given
    *context_data*, *data* and *options*

    *context_data* : Context dictionary of the current asset. Should contain the keys
    asset_type_name, asset_name, asset_id, version_number, version_id, context_id.

    *data* : Data of the current operation or plugin. Should contain the
    component_path from the asset that we are working on.

    *options* : Options of the current widget or operation, should contain the
    load_mode that we want to/or had apply to the current asset.

    *session* : should be instance of :class:`ftrack_api.session.Session`
    to use for communication with the server.
    '''

    arguments_dict = {}

    arguments_dict[constants.ASSET_NAME] = context_data.get(
        'asset_name', 'No name found'
    )
    arguments_dict[constants.ASSET_TYPE_NAME] = context_data.get(
        constants.ASSET_TYPE_NAME, ''
    )
    arguments_dict[constants.ASSET_ID] = context_data.get(
        constants.ASSET_ID, ''
    )
    arguments_dict[constants.VERSION_NUMBER] = int(
        context_data.get(constants.VERSION_NUMBER, 0)
    )
    arguments_dict[constants.VERSION_ID] = context_data.get(
        constants.VERSION_ID, ''
    )

    arguments_dict[constants.LOAD_MODE] = options.get(
        constants.LOAD_MODE, 'Not Set'
    )

    arguments_dict[constants.ASSET_INFO_OPTIONS] = options.get(
        constants.ASSET_INFO_OPTIONS, ''
    )

    arguments_dict[constants.ASSET_INFO_ID] = uuid.uuid4().hex

    asset_version_entity = session.query(
        'select version from AssetVersion where id is "{}"'.format(
            arguments_dict[constants.VERSION_ID]
        )
    ).one()

    asset_entity = asset_version_entity['asset']
    ancestors = asset_entity['ancestors']
    project_name = asset_entity['parent']['project']['name']
    context_path = "{}:{}:{}".format(
        project_name,
        ":".join(x['name'] for x in ancestors),
        asset_entity['name'],
    )
    arguments_dict[constants.CONTEXT_PATH] = context_path

    arguments_dict[constants.IS_LATEST_VERSION] = asset_version_entity[
        constants.IS_LATEST_VERSION
    ]

    dependencies = asset_version_entity['uses_versions']
    arguments_dict[constants.DEPENDENCY_IDS] = [
        dependency['id'] for dependency in dependencies
    ]

    location = session.pick_location()

    for component in asset_version_entity['components']:
        if location.get_component_availability(component) < 100.0:
            continue
        component_path = location.get_filesystem_path(component)
        for collector in data:
            if component_path in collector['result'][0]:
                arguments_dict[constants.COMPONENT_NAME] = component['name']
                arguments_dict[constants.COMPONENT_ID] = component['id']
                arguments_dict[constants.COMPONENT_PATH] = component_path

    arguments_dict[constants.IS_LOADED] = False

    return arguments_dict


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
    def from_version_entity(cls, version_entity, component_name):
        '''
        Returns an :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` object
        generated from the given *ftrack_version* and the given *component_name*

        *ftrack_version* : :class:`ftrack_api.entity.asset_version.AssetVersion`

        *component_name* : Component name

        '''
        asset_info_data = {}
        asset_entity = version_entity['asset']

        asset_info_data[constants.ASSET_NAME] = asset_entity['name']
        asset_info_data[constants.ASSET_TYPE_NAME] = asset_entity['type'][
            'name'
        ]
        asset_info_data[constants.ASSET_ID] = asset_entity['id']
        asset_info_data[constants.VERSION_NUMBER] = int(
            version_entity['version']
        )
        asset_info_data[constants.VERSION_ID] = version_entity['id']
        asset_info_data[constants.IS_LATEST_VERSION] = version_entity[
            constants.IS_LATEST_VERSION
        ]

        ancestors = asset_entity['ancestors']
        project_name = asset_entity['parent']['project']['name']
        context_path = "{}:{}:{}".format(
            project_name,
            ":".join(x['name'] for x in ancestors),
            asset_entity['name'],
        )
        asset_info_data[constants.CONTEXT_PATH] = context_path

        location = version_entity.session.pick_location()

        # Get dependencies
        dependencies = version_entity['uses_versions']
        asset_info_data[constants.DEPENDENCY_IDS] = [
            dependency['id'] for dependency in dependencies
        ]

        asset_info_data[constants.ASSET_INFO_ID] = uuid.uuid4().hex

        for component in version_entity['components']:
            if component['name'] == component_name:
                if location.get_component_availability(component) == 100.0:
                    component_path = location.get_filesystem_path(component)
                    if component_path:

                        asset_info_data[constants.COMPONENT_NAME] = component[
                            'name'
                        ]

                        asset_info_data[constants.COMPONENT_ID] = component[
                            'id'
                        ]

                        asset_info_data[
                            constants.COMPONENT_PATH
                        ] = component_path

        asset_info_data[constants.IS_LOADED] = False

        return cls(asset_info_data)
