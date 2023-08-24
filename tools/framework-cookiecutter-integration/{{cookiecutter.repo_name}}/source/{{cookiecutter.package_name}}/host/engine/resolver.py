# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from {{cookiecutter.package_name}} import utils as {{cookiecutter.host_type}}_utils
from {{cookiecutter.package_name}}.constants import asset as asset_const
from {{cookiecutter.package_name}}.constants.asset import modes as modes_const
from {{cookiecutter.package_name}}.asset import {{cookiecutter.host_type_capitalized}}FtrackObjectManager
from {{cookiecutter.package_name}}.asset.dcc_object import {{cookiecutter.host_type_capitalized}}DccObject


class {{cookiecutter.host_type_capitalized}}ResolverEngine(ResolverEngine):

    engine_type = core_constants.RESOLVER

    def __init__(
        self, event_manager, host_types, host_id, asset_type_name=None
    ):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type_name*'''
        super({{cookiecutter.host_type_capitalized}}ResolverEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name=asset_type_name
        )
