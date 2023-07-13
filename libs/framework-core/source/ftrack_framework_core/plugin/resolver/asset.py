# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import constants
from ftrack_framework_core.plugin import base


class AssetResolverPlugin(base.BaseActionPlugin):
    '''
    Class representing an Asset resolver Plugin. Inherits from
    :class:`~ftrack_framework_core.plugin.base.BaseActionPlugin`
    '''

    return_type = dict
    '''Type of object that should be returned'''
    plugin_type = constants.PLUGIN_ASSET_RESOLVE_TYPE
    '''Plugin type of the current plugin'''
    _required_output = []

    def __init__(self, session):
        '''
        Initialise ActionPlugin with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(AssetResolverPlugin, self).__init__(session)
