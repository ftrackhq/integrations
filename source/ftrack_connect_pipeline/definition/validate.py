# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import copy
import json
import python_jsonschema_objects as pjo
import logging

logger = logging.getLogger(__name__)


def _validate_and_augment_schema(schema, definition, type):
    '''
    Augments the given *definition* ot he given *type* with the
    given *schema*
    '''
    builder = pjo.ObjectBuilder(schema)
    ns = builder.build_classes(standardize_names=False)
    ObjectBuilder = getattr(ns, type.capitalize())
    klass = ObjectBuilder(**definition)
    serialised_data = klass.serialize()
    return json.loads(serialised_data)


def validate_schema(data):
    '''
    Validates and aguments the definitions and the schemas from the given *data*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`collect_definitions`
    '''
    copy_data = copy.deepcopy(data)
    # validate schema
    for schema in data['schema']:
        for entry in ['loader', 'publisher', 'package', 'asset_manager']:
            if schema['title'].lower() == entry:
                for definition in data[entry]:
                    augumented_valid_data = None
                    try:
                        augumented_valid_data = _validate_and_augment_schema(
                            schema, definition, entry
                        )
                    except Exception as error:
                        logger.error(
                            '{} {} does not match any schema. {}'.format(
                                entry, definition['name'], str(error)
                            )
                        )
                        copy_data[entry].remove(definition)
                        continue

                    copy_data[entry].remove(definition)
                    copy_data[entry].append(augumented_valid_data)

    return copy_data


def validate_asset_types(data, session):
    '''
    Validates that the asset types definned on the package definitions in the
    given *data* are valid asset types on ftrack.

    *data* : Dictionary of json definitions and schemas generated at
    :func:`collect_definitions`
    *session* : instance of :class:`ftrack_api.session.Session`
    '''
    # validate package asset types:
    copy_data = copy.deepcopy(data)
    valid_assets_types = [
        type['short']
        for type in session.query('select short from AssetType').all()
    ]

    for schema in data['schema']:
        for entry in ['loader', 'publisher']:
            if schema['title'].lower() == entry:
                if entry['asset_type'] not in valid_assets_types:
                    logger.error(
                        'Package {} does use a non existing'
                        ' asset type: {}'.format(
                            entry['name'], entry['asset_type']
                        )
                    )
                    copy_data['schema'].pop(
                        copy_data['schema'].index(entry)
                    )

    return copy_data

