# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

import python_jsonschema_objects as pjo

logger = logging.getLogger(__name__)


def _get_schema(schema_name, schemas):
    '''
    Returns the schema in the given *schemas* for the given *tool_config_type*

    *tool_config_type* : Type of the tool_config. (asset_manager, publisher...)

    *schemas* : List of schemas.
    '''
    for schema in schemas:
        if schema_name.lower() == schema['title'].lower():
            return schema
    return None


def validate_tool_config(schemas, tool_config):
    '''
    Validates the schema of the given *tool_config* from the given *schemas*
    using the _validate_jsonschema function of the jsonschema.validate library.

    *schemas* : List of schemas.

    *tool_config* : Tool config to be validated against the schema.
    '''
    # builder = pjo.ObjectBuilder(
    #     schemas[tool_config['validation_schema']], resolved=schemas
    # )
    # TODO: Double check if we get the ABCMeta error validating the definiition.
    #  If that occurs is because the pjo library gets corrupted when it executes
    #  build_classes during the augment
    # builder.validate(tool_config)

    # Returning Always true until above error is fixed.
    return True
