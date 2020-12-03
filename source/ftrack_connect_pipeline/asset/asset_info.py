# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import json
import uuid
import ftrack_api
from ftrack_connect_pipeline.constants import asset as constants


def generate_asset_info_dict_from_args(context, data, options, session):
    '''
    Returns a diccionary constructed from the needed values of the given
    *context*, *data* and *options*

    *context* : Context dictionary of the current asset. Should contain the keys
    asset_type, asset_name, asset_id, version_number, version_id, context_id.

    *data* : Data of the current operation or plugin. Should contain the
    component_path from the asset that we are working on.

    *options* : Options of the current widget or operation, should contain the
    load_mode that we want to/or had apply to the current asset.

    *session* : should be instance of :class:`ftrack_api.session.Session`
    to use for communication with the server.
    '''
    arguments_dict = {}

    arguments_dict[constants.ASSET_NAME] = context.get(
        'asset_name', 'No name found'
    )
    arguments_dict[constants.ASSET_TYPE] = context.get(constants.ASSET_TYPE, '')
    arguments_dict[constants.ASSET_ID] = context.get(constants.ASSET_ID, '')
    arguments_dict[constants.VERSION_NUMBER] = int(
        context.get(constants.VERSION_NUMBER, 0)
    )
    arguments_dict[constants.VERSION_ID] = context.get(constants.VERSION_ID, '')

    arguments_dict[constants.LOAD_MODE] = options.get(
        constants.LOAD_MODE, 'Not Set'
    )

    arguments_dict[constants.ASSET_INFO_OPTIONS] = options.get(
        constants.ASSET_INFO_OPTIONS, ''
    )

    arguments_dict[constants.ASSET_INFO_ID] = uuid.uuid4()

    asset_version = session.query(
        'select version from AssetVersion where id is "{}"'.format(
            arguments_dict[constants.VERSION_ID]
        )
    ).one()


    arguments_dict[constants.IS_LATEST_VERSION] = asset_version[
        constants.IS_LATEST_VERSION
    ]


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
            if v == unicode(None):
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
        return json.dumps(asset_info_options).encode('base64')

    def decode_options(self, asset_info_options):
        '''
        Decodes the json value from the given *asset_info_opitons*
        from base64.

        *asset_info_opitons* : Options used to load the asset in the scene.
        '''
        if not asset_info_options:
            self.logger.error("asset_info_options is empty")
        return json.loads(asset_info_options.decode('base64'))

    def __getitem__(self, k):
        '''
        Get the value from the given *k*

        Note:: In case of the given *k* is the asset_info_options it will
        automatically return the decoded json. Also if the given *k* is versions
        it will automatically download the current asset_versions from ftrack
        '''

        value = super(FtrackAssetInfo, self).__getitem__(k)
        if k == constants.ASSET_INFO_OPTIONS:
            if value:
                value = self.decode_options(value)
        if k == constants.VERSIONS:
            value = self._get_ftrack_versions()
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
        if k == constants.VERSIONS:
            new_value = self._get_ftrack_versions()
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

    def _get_ftrack_versions(self):
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
    def from_ftrack_version(cls, ftrack_version, component_name):
        '''
        Returns an :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` object
        generated from the given *ftrack_version* and the given *component_name*

        *ftrack_version* : :class:`ftrack_api.entity.asset_version.AssetVersion`

        *component_name* : Component name

        '''
        asset_info_data = {}
        asset = ftrack_version['asset']

        asset_info_data[constants.ASSET_NAME] = asset['name']
        asset_info_data[constants.ASSET_TYPE] = asset['type']['name']
        asset_info_data[constants.ASSET_ID] = asset['id']
        asset_info_data[constants.VERSION_NUMBER] = int(
            ftrack_version['version'])
        asset_info_data[constants.VERSION_ID] = ftrack_version['id']
        asset_info_data[constants.IS_LATEST_VERSION] = ftrack_version[
            constants.IS_LATEST_VERSION
        ]

        location = ftrack_version.session.pick_location()

        asset_info_data[constants.ASSET_INFO_ID] = uuid.uuid4()

        for component in ftrack_version['components']:
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