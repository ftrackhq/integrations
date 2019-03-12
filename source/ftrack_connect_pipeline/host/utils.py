# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import itertools
logger = logging.getLogger(__name__)


def merge_list(list_data):
    '''Utility function to merge *list_data*'''
    logger.debug('Merging {} '.format(list_data))
    list_data = list_data or []
    result = list(set(itertools.chain.from_iterable(list_data)))
    logger.debug('into {}'.format(result))
    return result


def merge_dict(dict_data):
    '''Utility function to merge *dict_data*'''
    logger.debug('Merging {} '.format(dict_data))
    dict_data = dict_data or {}
    result = {k: v for d in dict_data for k, v in d.items()}
    logger.debug('into {}'.format(result))
    return result


