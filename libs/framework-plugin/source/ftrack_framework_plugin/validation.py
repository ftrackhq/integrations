# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

logger = logging.getLogger(__name__)

def validate_output_type(result_type, required_type):
    if not isinstance(result_type, required_type):
        return False
    return True

def validate_output_value(result, required_value):
    if not required_value:
        return True
    if type(result) == dict:
        if type(required_value) != dict:
            return False
        valid_keys = _validate_dict_keys(result.keys(), required_value.keys())
        valid_values = _validate_dict_values(result.values(), required_value.values())
        if valid_values and valid_keys:
            return True
    return result == required_value

def _validate_dict_keys(result_keys, required_keys):
    if sorted(result_keys) == sorted(required_keys)
        return True
    return False

def _validate_dict_values(result_values, required_values):
    if sorted(result_values) == sorted(required_values)
        return True
    return False
