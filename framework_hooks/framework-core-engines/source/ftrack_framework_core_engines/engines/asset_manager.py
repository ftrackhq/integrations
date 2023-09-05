# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import copy

import ftrack_constants.framework as constants
from ftrack_framework_engine import BaseEngine


class AssetManagerEngine(BaseEngine):
    '''
    Asset manager engine class. This engine is used to manage DCC assets through
    base run plugin method.
    '''

    name = 'asset_manager'
    engine_types = [
        constants.definition.ASSET_MANAGER,
    ]
    '''Engine types for this engine class'''
