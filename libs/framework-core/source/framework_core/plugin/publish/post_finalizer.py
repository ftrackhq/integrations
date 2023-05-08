# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os

from framework_core import constants
from framework_core.plugin import base


class PublisherPostFinalizerPlugin(base.BasePostFinalizerPlugin):
    '''
    Base Publisher Post Finalizer Plugin Class inherits from
    :class:`~framework_core.plugin.base.BasePostFinalizerPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_PUBLISHER_POST_FINALIZER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return exporters'''
    version_dependencies = []
    '''Ftrack dependencies of the current asset version'''

    def __init__(self, session):
        super(PublisherPostFinalizerPlugin, self).__init__(session)
