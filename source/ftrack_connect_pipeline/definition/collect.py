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
    '''
    Resolves the refs of the schemas in the given *data*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`collect_definitions`
    '''
    data['schema'] = [
        JsonRef.replace_refs(schema) for schema in data['schema']
    ]
    return data


def filter_definitions_by_host(data, host_type):
    '''
    Filter the definitions in the given *data* by the given *host*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`collect_definitions`
    *host* : Type of definition host to be filtered by.
    '''
    copy_data = copy.deepcopy(data)
    logger.debug('filtering definition for host_type: {}'.format(host_type))
    for entry in ['loader', 'opener', 'publisher', 'asset_manager']:
        for definition in data[entry]:
            if str(definition.get('host_type')) != str(host_type):
                logger.debug(
                    'Removing definition for host_type: {}'.format(
                        definition.get('host_type')
                    )
                )
                copy_data[entry].remove(definition)

    return copy_data


def collect_definitions(lookup_dir):
    '''
    Collect all the schemas and definitions from the given
    *lookup_dir*

    *lookup_dir* : Directory path to look for the definitions.
    '''
    schemas = _collect_json(os.path.join(lookup_dir, 'schema'))

    loaders = _collect_json(os.path.join(lookup_dir, 'loader'))

    openers = _collect_json(os.path.join(lookup_dir, 'opener'))

    publishers = _collect_json(os.path.join(lookup_dir, 'publisher'))

    asset_managers = _collect_json(os.path.join(lookup_dir, 'asset_manager'))

    data = {
        'schema': schemas or [],
        'publisher': publishers or [],
        'loader': loaders or [],
        'opener': openers or [],
        'asset_manager': asset_managers or [],
    }

    return data


def _collect_json(source_path):
    '''
    Return a json encoded list of all the json files discovered in the given
    *source_path*.
    '''
    logger.debug('looking for definitions in : {}'.format(source_path))

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
                logger.error(
                    "{0} could not be registered, reason: {1}".format(
                        _file, str(error)
                    )
                )
        if data_store:
            loaded_jsons.append(data_store)

    return loaded_jsons
