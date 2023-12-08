# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_engine import BaseEngine


class StandardEngine(BaseEngine):
    '''
    StandardEngine class.
    '''

    name = 'standard_engine'

    def get_store(self) -> dict:
        return dict()
