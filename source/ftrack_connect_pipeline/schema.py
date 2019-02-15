from jsonschema import validate as _validate
from ftrack_connect_pipeline.session import get_shared_session
session = get_shared_session()

_context_types = [str(t['name']) for t in session.query('ObjectType').all()]
_asset_types = [str(t['short']) for t in session.query('AssetType').all()]

_plugin_schema = {
    "type": "object",
    "properties": {
        "plugins": {
            "type": "array",
            "items": {
                "type": "object",
            }
        }
    }

}


_publish_schema = {
    "type" : "object",
    "properties": {
        "plugins": {
            "type": "array",
            "items": {
                "type": 'object'
            }
        },
    }
}


asset_schema = {
     "type" : "object",
     "properties" : {
         "asset_name" : {
             "type" : "string"
         },
         "asset_type" : {
             "type" : "string",
             "enum": _asset_types
         },
         "context": {
             "type": "array",
             "items": {
                 "type": "string",
                 "enum": _context_types
            }
         },
         'publish': _publish_schema,
         'load': _publish_schema
    },
}


def validate(schema):
    _validate(schema, asset_schema)