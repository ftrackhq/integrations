# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

logger = logging.getLogger(__name__)


def validate_output_type(result_type, required_type):
    if not result_type == required_type:
        return False
    return True


def validate_output_value(result, required_value):
    if not required_value:
        return True
    valid_values = True
    if type(result) == dict:
        if type(required_value) != dict:
            return False
        valid_keys = validate_dict_keys(list(result.keys()), list(required_value.keys()))
        if any(required_value.values()):
            valid_values = validate_dict_values(list(result.values()), list(required_value.values()))
        if valid_values and valid_keys:
            return True
    return result == required_value


def validate_dict_keys(result_keys, required_keys):
    if all(item in result_keys for item in required_keys):
        return True
    return False


def validate_dict_values(result_values, required_values):
    if sorted(result_values) == sorted(required_values):
        return True
    return False
