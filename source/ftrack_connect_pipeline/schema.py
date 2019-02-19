from jsonschema import validate as _validate
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline import constants

session = get_shared_session()

_context_types = [str(t["name"]) for t in session.query("ObjectType").all()]
_asset_types = list(set([str(t["short"]) for t in session.query("AssetType").all()]))


_plugin_schema = {
    "type": "object",
    "required": [
        "name", "plugin"
    ],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "plugin": {"type": "string"},
        "options": {"type": "object"},
        "description": {"type": "string"},
        "widget": {"type": "string"},
        "visible": {"type": "boolean"}
    }
}


_publish_plugins_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        constants.CONTEXT :{
            "type": "array",
            "items": _plugin_schema
        },
        constants.COLLECTORS: {
            "type": "array",
            "items": _plugin_schema
        },
        constants.VALIDATORS: {
            "type": "array",
            "items": _plugin_schema
        },
        constants.EXTRACTORS: {
            "type": "array",
            "items": _plugin_schema
        },
        constants.PUBLISHERS: {
            "type": "array",
            "items": _plugin_schema
        }
    }
}

_load_plugins_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        constants.CONTEXT :{
            "type": "array",
            "items": _plugin_schema
        },
        constants.IMPORTERS: {
            "type": "array",
            "items": _plugin_schema
        }
    }
}


_publish_schema = {
    "type" : "object",
    "additionalProperties": False,
    "properties": {
        "plugins": {
            "type": "array",
            "items": _publish_plugins_schema
        },
    }
}


_load_schema = {
    "type" : "object",
    "additionalProperties": False,
    "properties": {
        "plugins": {
            "type": "array",
            "items": _load_plugins_schema
        },
    }
}

asset_schema = {
    "type" : "object",
    "required": [
        "asset_name",
        "asset_type",
        "context",
        "publish"
    ],
    "additionalProperties": False,
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
         "publish": _publish_schema,
         "load": _load_schema
    }
}


def validate(schema):
    _validate(schema, asset_schema)