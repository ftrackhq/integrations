# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import logging
from ftrack_connect_pipeline.host import Host
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_{{cookiecutter.host_type}} import constants as {{cookiecutter.host_type}}_constants
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.host import engine as host_engine

logger = logging.getLogger(__name__)


class {{cookiecutter.host_type_capitalized}}Host(Host):
    '''
    {{cookiecutter.host_type_capitalized}}Host class.
    '''

    host_types = [qt_constants.HOST_TYPE, {{cookiecutter.host_type}}_constants.HOST_TYPE]
    # Define the {{cookiecutter.host_type_capitalized}} engines to be run during the run function
    engines = {
        'asset_manager': host_engine.{{cookiecutter.host_type_capitalized}}AssetManagerEngine,
        'loader': host_engine.{{cookiecutter.host_type_capitalized}}LoaderEngine,
        'opener': host_engine.{{cookiecutter.host_type_capitalized}}OpenerEngine,
        'publisher': host_engine.{{cookiecutter.host_type_capitalized}}PublisherEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize {{cookiecutter.host_type_capitalized}}Host with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super({{cookiecutter.host_type_capitalized}}Host, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super({{cookiecutter.host_type_capitalized}}Host, self).run(event)
        return runnerResult
