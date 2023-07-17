# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import copy
import json
import python_jsonschema_objects as pjo
import logging

from ftrack_framework_core import constants

logger = logging.getLogger(__name__)


# TODO: move the definitions validators to a new validators folder
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


def validate_schema(data, session):
    '''
    Validates and aguments the definitions and the schemas from the given *data*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`collect_definitions`
    '''
    copy_data = copy.deepcopy(data)
    valid_assets_types = [
        type['short']
        for type in session.query('select short from AssetType').all()
    ]

    # validate schema
    for schema in data['schema']:
        # TODO: these keys should be constants
        for entry in [
            constants.LOADER,
            constants.OPENER,
            constants.PUBLISHER,
            constants.ASSET_MANAGER,
            constants.RESOLVER,
        ]:
            if schema['title'].lower() == entry:
                for definition in data[entry]:
                    copy_data[entry].remove(definition)
                    if schema['title'].lower() not in [
                        constants.ASSET_MANAGER,
                        constants.RESOLVER,
                    ]:
                        if (
                            definition.get('asset_type')
                            not in valid_assets_types
                        ):
                            logger.error(
                                'Definition {} does use a non existing'
                                ' asset type: {}'.format(
                                    definition['name'],
                                    definition.get('asset_type'),
                                )
                            )
                            continue

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

                        continue
                    copy_data[entry].append(augumented_valid_data)

    return copy_data
