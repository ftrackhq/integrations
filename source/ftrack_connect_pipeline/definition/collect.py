# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import fnmatch
import os
import logging
import copy
from jsonref import JsonRef
logger = logging.getLogger(__name__)


def resolve_schemas(data):
    data['schema'] = [JsonRef.replace_refs(schema) for schema in data['schema']]
    return data


def filter_definitions_by_host(data, host):
    copy_data = copy.deepcopy(data)
    logger.info('filtering definition for host: {}'.format(host))
    for entry in ['loader', 'publisher']:
        for definition in data[entry]:
            if str(definition.get('host')) != str(host):
                logger.warning(
                    'Removing definition for host: {}'.format(
                        definition.get('host')
                    )
                )
                copy_data[entry].remove(definition)

    return copy_data


def collect_definitions(lookup_dir):
    schemas = _collect_json(
        os.path.join(lookup_dir, 'schema')
    )

    packages = _collect_json(
        os.path.join(lookup_dir, 'package')
    )

    loaders = _collect_json(
        os.path.join(lookup_dir, 'loader')
    )

    publishers = _collect_json(
        os.path.join(lookup_dir, 'publisher')
    )

    data = {
        'schema': schemas or [],
        'publisher': publishers or [],
        'loader': loaders or [],
        'package': packages or []
    }

    return data


def _collect_json(source_path):
    '''
    Return a json encoded list of all the json files discovered in the given
    *source_path*.
    '''
    logger.debug('looking for dernitions in : {}'.format(source_path))

    json_files = []
    for root, dirnames, filenames in os.walk(source_path):
        for filename in fnmatch.filter(filenames, '*.json'):
            json_files.append(os.path.join(root, filename))

    loaded_jsons = []
    for json_file in json_files:
        data_store = None
        with open(json_file, 'r') as _file:
            try:
                data_store = json.load(_file)
            except Exception as error:
                logger.warning(
                    "{0} could not be registered, reason: {1}".format(
                        _file, str(error)
                    )
                )
        if data_store:
            loaded_jsons.append(data_store)

    return loaded_jsons

