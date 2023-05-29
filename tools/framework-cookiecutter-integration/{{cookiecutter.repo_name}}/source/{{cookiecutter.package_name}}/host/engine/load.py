# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline.host.engine import LoaderEngine


class {{cookiecutter.host_type_capitalized}}LoaderEngine(LoaderEngine):
    engine_type = 'loader'

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        '''Initialise LoaderEngine with *event_manager*, *host*, *hostid* and
        *asset_type_name*'''
        super({{cookiecutter.host_type_capitalized}}LoaderEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
