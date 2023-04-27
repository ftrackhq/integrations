# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class PublisherPreFinalizerPlugin(base.BasePreFinalizerPlugin):
    '''
    Base Publisher Pre Finalizer Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BasePreFinalizerPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_PUBLISHER_PRE_FINALIZER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return exporters'''
    version_dependencies = []
    '''Ftrack dependencies of the current asset version'''

    def __init__(self, session):
        super(PublisherPreFinalizerPlugin, self).__init__(session)
