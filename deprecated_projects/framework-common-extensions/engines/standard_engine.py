# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.engine import BaseEngine


class StandardEngine(BaseEngine):
    '''
    StandardEngine class.
    '''

    name = 'standard_engine'

    def get_store(self) -> dict:
        return dict()
