# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import logging
from ftrack_connect_pipeline.host import Host
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_{{cookiecutter.host_type}} import constants as {{cookiecutter.host_type}}_constants
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.host import engine as host_engine

logger = logging.getLogger(__name__)


class {{cookiecutter.host_type|capitalize}}Host(Host):
    '''
    {{cookiecutter.host_type|capitalize}}Host class.
    '''

    host_types = [qt_constants.HOST_TYPE, {{cookiecutter.host_type}}_constants.HOST_TYPE]
    # Define the {{cookiecutter.host_type|capitalize}} engines to be run during the run function
    engines = {
        'asset_manager': host_engine.{{cookiecutter.host_type|capitalize}}AssetManagerEngine,
        'loader': host_engine.{{cookiecutter.host_type|capitalize}}LoaderEngine,
        'opener': host_engine.{{cookiecutter.host_type|capitalize}}OpenerEngine,
        'publisher': host_engine.{{cookiecutter.host_type|capitalize}}PublisherEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize {{cookiecutter.host_type|capitalize}}Host with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super({{cookiecutter.host_type|capitalize}}Host, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super({{cookiecutter.host_type|capitalize}}Host, self).run(event)
        return runnerResult
