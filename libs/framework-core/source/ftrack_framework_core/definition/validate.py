# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging

from jsonschema import validate as _validate_jsonschema

logger = logging.getLogger(__name__)

def _get_schema(definition_type, schemas):
    '''
    Returns the schema in the given *schemas* for the given *definition_type*

    *definition_type* : Type of the definition. (asset_manager, publisher...)

    *schemas* : List of schemas.
    '''
    for schema in schemas:
        if definition_type == schema['title'].lower():
            return schema
    return None


# TODO: this should be moved to validate folder with the definitions
def validate_definition(schemas, definition):
    '''
    Validates the schema of the given *definition* from the given *schemas*
    using the _validate_jsonschema function of the jsonschema.validate library.

    *schemas* : List of schemas.

    *definition* : Definition to be validated against the schema.
    '''
    schema = _get_schema(definition['type'], schemas)
    _validate_jsonschema(definition, schema)



