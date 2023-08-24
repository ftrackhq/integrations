# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import logging
from ftrack_connect_pipeline.host import Host
from ftrack_framework_core import constants as core_constants
from ftrack_connect_pipeline_qt import constants as qt_constants
from {{cookiecutter.package_name}} import constants as {{cookiecutter.host_type}}_constants
from {{cookiecutter.package_name}}.host import engine as host_engine

logger = logging.getLogger(__name__)


class {{cookiecutter.host_type_capitalized}}Host(Host):
    '''
    {{cookiecutter.host_type_capitalized}}Host class.
    '''

    host_types = [qt_constants.HOST_TYPE, {{cookiecutter.host_type}}_constants.HOST_TYPE]
    # Define the {{cookiecutter.host_type_capitalized}} engines to be run during the run function
    engines = {
        core_constants.PUBLISHER: host_engine.{{cookiecutter.host_type_capitalized}}PublisherEngine,
        core_constants.LOADER: host_engine.{{cookiecutter.host_type_capitalized}}LoaderEngine,
        core_constants.OPENER: host_engine.{{cookiecutter.host_type_capitalized}}OpenerEngine,
        core_constants.ASSET_MANAGER: host_engine.{{cookiecutter.host_type_capitalized}}AssetManagerEngine,
        core_constants.RESOLVER: host_engine.{{cookiecutter.host_type_capitalized}}ResolverEngine,
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
