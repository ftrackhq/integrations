# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from jsonschema import validate as _validate
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline import constants

session = get_shared_session()

_context_types = [str(t["name"]) for t in session.query("ObjectType").all()]
_asset_types = list(set([str(t["short"]) for t in session.query("AssetType").all()]))

# Stage Plugin Schema

_plugin_schema = {
    "type": "object",
    "required": [
        "name", "plugin"
    ],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "plugin": {"type": "string"},
        "widget": {"type": "string"},
        "visible": {"type": "boolean"},
        "editable": {"type": "boolean"},
        "disabled": {"type": "boolean"},
        "options": {"type": "object"},

    }
}

# Package schema

package_component_schema = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "name"
    ],
    "properties": {
        "name": {"type": "string"},
        "file_type": {"type": "array", "items":{"type": "string"}},
        "optional": {"type": "boolean"}
    }
}


package_schema = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "name", "type", "context", "components"
    ],
    "properties":{
        "name": {"type" : "string"},
        "type": {"type": "string", "enum": _asset_types},
        "context": {
            "type": "array",
            'minItems': 1,
            "items": {
                "type": "string",
                "enum": _context_types
            }
        },
        "components":{
            "type": "array",
            "items": package_component_schema,
            'minItems': 1
        },
    }

}

# Package publisher Schema


publisher_schema = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "name", "package", "host", "ui", "context", "components", "publish"
    ],
    "properties": {
        "name": {"type": "string"},
        "package": {"type": "string"},
        "host": {"type": "string"},
        "ui": {"type": "string"},
        constants.CONTEXT: {
            "type": "array",
            "items": _plugin_schema,
            'minItems': 1,
            'maxItems': 1,
        },
        "components": {
            "type": "object",
            "properties": {
                constants.COLLECT: {
                    "type": "array",
                    "items": _plugin_schema,
                    'minItems': 1,
                    'uniqueItems': True
                },
                constants.VALIDATE: {
                    "type": "array",
                    "items": _plugin_schema,
                    'minItems': 1,
                    'uniqueItems': True
                },
                constants.OUTPUT: {
                    "type": "array",
                    "items": _plugin_schema,
                    'maxItems': 1,
                    'minItems': 1,
                    'uniqueItems': True
                }
            }
        },
        constants.PUBLISH: {
            "type": "array",
            "items": _plugin_schema,
            'minItems': 1,
            'uniqueItems': True
        }
    }
}

# Package loader Schema

loader_schema = {
    "type": "object",
    "required": [
        "host", "ui"
    ],
    "properties": {
        "name": {"type": "string"},
        "host": {"type": "string"},
        "ui": {"type": "string"},
        "components": {
            "type": "array",
            "items": _plugin_schema
        },
        "post": {
            "type": "array",
            "items": _plugin_schema
        }
    }
}


def validate_package(schema):
    _validate(schema, package_schema)


def validate_publisher(schema):
    _validate(schema, publisher_schema)


def validate_loader(schema):
    _validate(schema, loader_schema)
