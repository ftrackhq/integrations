# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import re
import logging
import yaml

logger = logging.getLogger(__name__)


def read_yaml_file(file_path):
    '''Read the given *file_path* json file'''
    yaml_content = None
    if os.path.exists(file_path):
        with open(file_path, 'r') as yaml_file:
            try:
                yaml_content = yaml.safe_load(yaml_file)
            except yaml.YAMLError as exc:
                logger.error(
                    f"Invalid .yaml file\nFile: {file_path}\nError: {exc}"
                )
    else:
        logger.warning(f"file {file_path} doesn't exists")

    return yaml_content


def write_yaml_file(file_path, content):
    '''Write the given *file_path* YAML file with the given *content*.'''
    with open(file_path, 'w') as file:
        try:
            yaml.dump(content, file, default_flow_style=False, sort_keys=False)
        except Exception as e:
            logger.exception(
                f'Exception writing YAML file in {file_path}, error: {e}.'
            )


def resolve_placeholders(value, data):
    """
    Recursively resolve placeholders in a string value based on the provided data.
    :param value: The current string value potentially containing placeholders.
    :param data: The dictionary containing the values to replace placeholders.
    :return: The value with all placeholders resolved.
    """
    pattern = re.compile(r'\{\$(.*?)\}')
    while True:
        match = pattern.search(value)
        if not match:
            break
        placeholder = match.group(1)
        replacement = data.get(placeholder, '')
        if isinstance(replacement, list):
            new_values = []
            for obj in replacement:
                new_value = value.replace(match.group(), obj)
                new_values.append(new_value)
            return new_values
        else:
            value = value.replace(match.group(), replacement)
    return value


def substitute_placeholders(data, original_data):
    """
    Recursively substitute placeholders in the data structure with actual values from the same structure.
    :param data: The current data part being processed.
    :param original_data: The complete, original data structure for replacements.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = substitute_placeholders(value, original_data)
    elif isinstance(data, list):
        return [substitute_placeholders(item, original_data) for item in data]
    elif isinstance(data, str):
        return resolve_placeholders(data, original_data)
    return data
