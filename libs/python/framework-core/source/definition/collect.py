# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import json
import fnmatch
import os
import logging
import copy
from jsonref import JsonRef

from ftrack_connect_pipeline import constants

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


def filter_definitions_by_host(data, host_types):
    '''
    Filter the definitions in the given *data* by the given *host*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`collect_definitions`
    *host_types* : List of definition host to be filtered by.
    '''
    copy_data = copy.deepcopy(data)
    logger.debug('filtering definition for host_type: {}'.format(host_types))
    for entry in constants.DEFINITION_TYPES:
        for definition in data[entry]:
            if str(definition.get('host_type')) not in host_types:
                logger.debug(
                    'Removing definition for host_type: {}'.format(
                        definition.get('host_type')
                    )
                )
                copy_data[entry].remove(definition)

    return copy_data


def collect_definitions(definition_paths):
    '''
    Collect all the schemas and definitions from the given
    *definition_paths*

    *definition_paths* : Directory path to look for the definitions.
    '''
    data = {
        'schema': [],
        'publisher': [],
        'loader': [],
        'opener': [],
        'asset_manager': [],
    }
    for lookup_dir in definition_paths:
        for file_type in [
            'schema',
            'loader',
            'opener',
            'publisher',
            'asset_manager',
        ]:
            collected_files = _collect_json(
                os.path.join(lookup_dir, file_type)
            )
            data[file_type].extend(collected_files)
            logger.debug(
                'Found {} definitions in path: {}'.format(
                    len(collected_files), lookup_dir
                )
            )

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
