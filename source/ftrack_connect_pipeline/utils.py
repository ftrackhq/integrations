# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import itertools
import copy

import ftrack_api

from ftrack_connect_pipeline import constants

logger = logging.getLogger(__name__)


def merge_list(list_data):
    '''Utility function to merge *list_data*'''
    logger.info('Merging {} '.format(list_data))
    result = list(set(itertools.chain.from_iterable(list_data)))
    logger.info('into {}'.format(result))
    return result


def merge_dict(dict_data):
    '''Utility function to merge *dict_data*'''
    logger.info('Merging {} '.format(dict_data))
    result = {k: v for d in dict_data for k, v in d.items()}
    logger.info('into {}'.format(result))
    return result


class AssetSchemaManager(object):
    '''Asset schema manager class.'''

    @property
    def assets(self):
        '''return the registered assets.'''
        filtered_results = {}
        for asset_name, asset_data in self.asset_registry.items():
            if self._context_type in asset_data['context']:
                filtered_results[asset_name] = asset_data

        return copy.deepcopy(filtered_results)

    def __init__(self, session, context_type):
        '''Initialise the class with ftrack *session* and *context_type*'''
        self.asset_registry = {}
        self._context_type = context_type
        self.session = session
        self._register_assets()

    def _register_assets(self):
        '''register assets'''
        results = self.session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=constants.REGISTER_ASSET_TOPIC,
                data=dict()
            ),
            synchronous=True
        )
        for result in results[0]:
            self.asset_registry[result['asset_name']] = result
