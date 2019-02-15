from jsonschema import validate as _validate
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline import constants

session = get_shared_session()

_context_types = [str(t['name']) for t in session.query('ObjectType').all()]
_asset_types = list(set([str(t['short']) for t in session.query('AssetType').all()]))


_plugin_schema = {
    "type": "object",
    "properties": {
        "widget":       {"type": "string"},
        "plugin":       {"type": "string"},
        "name":         {"type": "string"},
        "options":      {"type": "object"},
        "description":  {"type": "string"},
    }
}


_publish_plugins_schema = {
    "type": "object",
    "propertyNames": {
        "enum": [
            constants.CONTEXT,
            constants.COLLECTORS,
            constants.VALIDATORS,
            constants.EXTRACTORS,
            constants.PUBLISHERS
        ],
        'type': _plugin_schema
    }
}


_publish_schema = {
    "type" : "object",
    "properties": {
        "plugins": {
            "type": "array",
            "items": _publish_plugins_schema
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
         'publish': _publish_schema
    }
}
from pprint import pformat
print pformat(asset_schema)

def validate(schema):
    _validate(schema, asset_schema)