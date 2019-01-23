import logging
import itertools


logger = logging.getLogger(__name__)


def merge_list(list_data):
    logger.info('Merging {} '.format(list_data))
    result = list(set(itertools.chain.from_iterable(list_data)))
    logger.info('into {}'.format(result))
    return result


def merge_dict(dict_data):
    logger.info('Merging {} '.format(dict_data))
    result = {k: v for d in dict_data for k, v in d.items()}
    logger.info('into {}'.format(result))
    return result
