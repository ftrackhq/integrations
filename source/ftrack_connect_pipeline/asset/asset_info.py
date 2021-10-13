# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import json
import uuid
import base64
import six
import ftrack_api
from ftrack_connect_pipeline.constants import asset as constants

def get_parent_dependency_recursive(parent):
    #TODO: fix this to avoid linked tasks
    dependencies = []
    if parent.entity_type == 'Project':
        return []
    for link in parent.get('incoming_links'):
        from_entity = link['from']
        if not from_entity['type']['name'] == 'Generic':
            dependencies.append(from_entity)
    if parent.get('parent'):
        dependencies.extend(get_parent_dependency_recursive(parent['parent']))
    return list(set(dependencies))

def get_all_dependencies(entity):
    #TODO: fix this to avoid linked tasks
    dependencies = []
    asset = entity
    if entity.entity_type == 'AssetVersion':
        for asset_ver_link in entity.get('incoming_links'):
            from_entity = asset_ver_link['from']
            if not from_entity['type']['name'] == 'Generic':
                dependencies.append(from_entity)
        asset = entity['asset']
    dependencies.extend(get_parent_dependency_recursive(asset['parent']))
    dependencies = list(set(dependencies))
    #Check if a lower lavel of an asset is already in the list
    duplicated = []
    for dependency in dependencies:
        for child in dependency['children']:
            if child in dependencies:
                duplicated.append(dependency)

    dependencies = list(set(dependencies) - set(duplicated))
    return dependencies

# def get_all_dependencies(asset_version_entity):
#     #TODO: fix this to avoid linked tasks
#     dependencies = []
#     for asset_ver_link in asset_version_entity.get('incoming_links'):
#         from_entity = asset_ver_link['from']
#         if not from_entity['type']['name'] == 'Generic':
#             dependencies.append(from_entity)
#     asset = asset_version_entity['asset']
#     dependencies.extend(get_parent_dependency_recursive(asset['parent']))
#     dependencies = list(set(dependencies))
#     #Check if a lower lavel of an asset is already in the list
#     duplicated = []
#     for dependency in dependencies:
#         for child in dependency['children']:
#             if child in dependencies:
#                 duplicated.append(dependency)
#
#     dependencies = list(set(dependencies) - set(duplicated))
#     return dependencies


def generate_asset_info_dict_from_args(context_data, data, options, session):
    '''
    Returns a diccionary constructed from the needed values of the given
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

    # TODO: we will have to extend this in order to represent an asset build
    #  instead of an asset. That is because in the asset manager we will have to
    #  deal with the dependencies as well and we can't control what a final user
    #  will link as dependency, so in the asset manager we will have to show or
    #  represent something like the following:
    #  (alternative) ---> Sequence / AssetBuild   |   Task (or type)    |   AssetName  |   version   | Component
    #  AssetBuild   |   Task    |   AssetName  |   version   | Component
    #  char01       |   Model   |   body_model_A    |   55        | abc
    #         prop01       |   Model   |   body_model_A    |   55        | abc
    #         prop02       |   Model   |   body_model_A    |   55        | abc
    #  char02       |   Model   |   body_model_A    |   55        | abc
    #         prop01       |   Model   |   body_model_A    |   55        | abc
    #               prop02       |   Model   |   body_model_A    |   55        | abc
    #  So if the dependency is linked to a specific asset version we can
    #  preselect all the options in the AM and let the user select the component,
    #  but if the dependency is linked to the asset build we will have to let
    #  the user select the task, the assetVariation, the version and the component.
    #  We will have to add the task somehow here... or instead add the type but
    #  the problem is that we can't link an asset with a specific type to a shot
    #  but we can link a specific task to a shot....
    #  Maybe we should linit it and don't let the user link task, instead they
    #  should allways link assetBuilds so then we make sure that we filter by
    #  type and we aboid having to chose the task. The biggest problem is that
    #  there is no way with ftrack to link the modeling of an asset into a shot
    #  because you could have 2 different modelling tasks in ftrack so isn't
    #  useful to link tasks.
    #  So my idea is something like this:
    #  : (also we should think about adding the sequence in some cases)
    #  AssetBuild   |   Type(Selectable By User)    |   AssetName(SBU)  |   version(SBU)   | Component(SBU)
    #  char01       |   Geometry   |   body_model_A    |   55        | abc
    #         prop01       |   Geometry   |   body_model_A    |   55        | abc
    #         prop02       |   Rigging   |   body_model_A    |   55        | abc
    #  char02       |   Shading   |   body_model_A    |   55        | abc
    #         prop01       |   Camera   |   body_model_A    |   55        | abc
    #               prop02       |   ImagePlane   |   body_model_A    |   55        | abc

    arguments_dict = {}

    arguments_dict[constants.ASSET_NAME] = context_data.get(
        'asset_name', 'No name found'
    )
    arguments_dict[constants.ASSET_TYPE_NAME] = context_data.get(constants.ASSET_TYPE_NAME, '')
    arguments_dict[constants.ASSET_ID] = context_data.get(constants.ASSET_ID, '')
    arguments_dict[constants.VERSION_NUMBER] = int(
        context_data.get(constants.VERSION_NUMBER, 0)
    )
    arguments_dict[constants.VERSION_ID] = context_data.get(constants.VERSION_ID, '')

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


    arguments_dict[constants.IS_LATEST_VERSION] = asset_version_entity[
        constants.IS_LATEST_VERSION
    ]

    #Get dependencies
    dependencies = get_all_dependencies(asset_version_entity)
    #With the dependency count we will check (sync) if there are new dependencies in ftrack
    arguments_dict[constants.DEPENDENCY_IDS] = [
        dependency['id'] for dependency in dependencies
    ]
    #Parenting the dependency id in order to call them with
    # session.query("TypedContext where id is 5258aeb6-06d0-11ea-bb4b-ee594985c7e2").first()
    # but bere in mind this doesn't work for asset_versions.
    # arguments_dict[constants.DEPENDENCIES] = []
    arguments_dict[constants.IS_DEPENDENCY] = False

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

    return arguments_dict


class FtrackAssetInfo(dict):
    '''
    Base FtrackAssetInfo class.
    '''

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._session

    @property
    def is_deprecated(self):
        '''
        Returns whether the current class is made up from a legacy mapping type
        of the asset_information.
        '''
        return self._is_deprecated_version

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
            if k == constants.SESSION and isinstance(v, ftrack_api.Session):
                self._session = v

        return new_mapping

    def __init__(self, mapping=None, **kwargs):
        '''
        Initialize the FtrackAssetInfo with the given *mapping*.

        *mapping* Dictionary with the asset information.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )
        self._session = None
        self._is_deprecated_version = False
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
            json.loads(base64.b64decode(asset_info_options))
        return json.loads(base64.b64decode(asset_info_options).decode('ascii'))

    def __getitem__(self, k):
        '''
        Get the value from the given *k*

        Note:: In case of the given *k* is the asset_info_options it will
        automatically return the decoded json. Also if the given *k* is asset_versions_entities
        it will automatically download the current asset_versions entities from
        ftrack
        '''

        value = super(FtrackAssetInfo, self).__getitem__(k)
        if k == constants.ASSET_INFO_OPTIONS:
            if value:
                value = self.decode_options(value)
        if k == constants.ASSET_VERSIONS_ENTITIES:
            value = self._get_asset_versions_entities()
        if k == constants.SESSION:
            if self.session:
                value = self.session
        return value

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k*

        Note:: In case of the given *k* is the asset_info_options it will
        automatically encode the given json value to base64
        '''

        if k == constants.ASSET_INFO_OPTIONS:
            v = self.encode_options(v)
        if k == constants.SESSION:
            if not isinstance(v, ftrack_api.Session):
                raise ValueError()
            self._session = v
        super(FtrackAssetInfo, self).__setitem__(k, v)

    def get(self, k, default=None):
        '''
        If exists, returns the value of the given *k* otherwise returns
        *default*.

        *k* : Key of the current dictionary.

        *default* : Default value of the given Key.
        '''
        value = super(FtrackAssetInfo, self).get(k, default)
        if k == constants.ASSET_VERSIONS_ENTITIES:
            new_value = self._get_asset_versions_entities()
            # Make sure that in case is returning None, set the default value
            if new_value:
                value = new_value
        return value

    def setdefault(self, k, default=None):
        '''
        Sets the *default* value for the given *k*.

        *k* : Key of the current dictionary.

        *default* : Default value of the given Key.
        '''
        if k == constants.SESSION:
            if not isinstance(default, ftrack_api.Session):
                raise ValueError()
            self._session = default
        super(FtrackAssetInfo, self).setdefault(k, default)

    def _get_asset_versions_entities(self):
        '''
        Return all the versions of the current asset_id
        Raises AttributeError if session is not set.
        '''
        if not self.session:
            raise AttributeError('asset_info.session has to be set before query '
                                 'versions')
        query = (
            'select is_latest_version, id, asset, components, components.name, '
            'components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}"'
            'order by version ascending'
        ).format(
            self[constants.ASSET_ID], self[constants.COMPONENT_NAME]
        )
        versions = self.session.query(query).all()
        return versions

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
        asset_info_data[constants.ASSET_TYPE_NAME] = asset_entity['type']['name']
        asset_info_data[constants.ASSET_ID] = asset_entity['id']
        asset_info_data[constants.VERSION_NUMBER] = int(
            version_entity['version'])
        asset_info_data[constants.VERSION_ID] = version_entity['id']
        asset_info_data[constants.IS_LATEST_VERSION] = version_entity[
            constants.IS_LATEST_VERSION
        ]

        location = version_entity.session.pick_location()

        #Get dependencies
        dependencies = get_all_dependencies(version_entity)
        #With the dependency count we will check (sync) if there are new dependencies in ftrack
        asset_info_data[constants.DEPENDENCY_IDS] = [
            dependency['id'] for dependency in dependencies
        ]
        #Parenting the dependency id in order to call them with
        # session.query("TypedContext where id is 5258aeb6-06d0-11ea-bb4b-ee594985c7e2").first()
        # but bere in mind this doesn't work for asset_versions.
        # asset_info_data[constants.DEPENDENCIES] = []

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

        return cls(asset_info_data)

    @classmethod
    def from_asset_build(cls, asset_build):
        '''
        Returns an :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` object
        generated from the given *ftrack_version* and the given *component_name*

        *ftrack_version* : :class:`ftrack_api.entity.asset_version.AssetVersion`

        *component_name* : Component name

        '''
        asset_info_data = {}

        #We don't have the type, assetName, the version or the component
        asset_info_data[constants.ASSET_NAME] = asset_build['name']
        asset_info_data[constants.ASSET_TYPE_NAME] = asset_build['type']['name']
        asset_info_data[constants.ASSET_ID] = asset_build['id']
        asset_info_data[constants.VERSION_NUMBER] = int(0)
        asset_info_data[constants.VERSION_ID] = ''
        asset_info_data[constants.IS_LATEST_VERSION] = False
        asset_info_data[constants.LOAD_MODE] = ''
        # TODO: Here we could probably pass how to load this assets so the
        #  loader for the dependencies, just changing the load mode to reference
        asset_info_data[constants.ASSET_INFO_OPTIONS] = ''

        dependencies = get_all_dependencies(asset_build)
        asset_info_data[constants.DEPENDENCY_IDS] = [
            dependency['id'] for dependency in dependencies
        ]
        asset_info_data[constants.ASSET_INFO_ID] = uuid.uuid4().hex
        asset_info_data[constants.COMPONENT_NAME] = ''
        asset_info_data[constants.COMPONENT_ID] = ''
        asset_info_data[constants.COMPONENT_PATH] = ''

        return cls(asset_info_data)