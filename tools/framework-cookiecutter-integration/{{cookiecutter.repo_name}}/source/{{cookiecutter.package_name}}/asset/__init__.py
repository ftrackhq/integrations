# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline.asset import FtrackObjectManager
from {{cookiecutter.package_name}}.asset.dcc_object import {{cookiecutter.host_type_capitalized}}DccObject


class {{cookiecutter.host_type_capitalized}}FtrackObjectManager(FtrackObjectManager):
    '''
    {{cookiecutter.host_type_capitalized}}FtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = {{cookiecutter.host_type_capitalized}}DccObject

    def __init__(self, event_manager):
        '''
        Initialize {{cookiecutter.host_type_capitalized}}FtrackObjectManager with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super({{cookiecutter.host_type_capitalized}}FtrackObjectManager, self).__init__(event_manager)
