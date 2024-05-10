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
    Recursively resolve placeholders in a string value or a list based on the provided data.
    When an environment variable resolves to a list, it's properly expanded.
    """
    pattern = re.compile(r'\$\{(.*?)\}')

    def resolve_string(s):
        """Resolve placeholders within a single string."""
        while True:
            match = pattern.search(s)
            if not match:
                break
            placeholder = match.group(1)
            keys = placeholder.split('.')
            if keys:
                replacement = data
                for key in keys:
                    if key in replacement:
                        replacement = replacement[key]
                    else:
                        replacement = None
            else:
                replacement = data.get(placeholder, os.getenv(placeholder, ''))
            # Split environment variable string into list if it contains path separator
            if isinstance(replacement, str) and os.pathsep in replacement:
                replacement = replacement.split(os.pathsep)
            # Handle replacement being a list
            if isinstance(replacement, list):
                # Generate new values for each list item
                return [
                    resolve_string(s.replace(match.group(), r, 1))
                    for r in replacement
                ]
            else:
                s = s.replace(match.group(), str(replacement), 1)
        return s

    if isinstance(value, str):
        return resolve_string(value)
    # TODO: The  elif isinstance(value, list): is not used right now, so we can decide to remove it
    elif isinstance(value, list):
        # Resolve each item in the list, handling nested lists from replacements
        resolved = [resolve_placeholders(item, data) for item in value]
        # Flatten the list if replacements introduced nested lists and remove duplicates
        flat_list = []
        for item in resolved:
            if isinstance(item, list):
                for sub_item in item:
                    if sub_item not in flat_list:
                        flat_list.append(sub_item)
            else:
                if item not in flat_list:
                    flat_list.append(item)
        return flat_list
    else:
        return value


def substitute_placeholders(data, original_data):
    """
    Recursively substitute placeholders in the data structure with actual values from the same structure.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = substitute_placeholders(value, original_data)
    elif isinstance(data, list):
        resolved = [
            substitute_placeholders(item, original_data) for item in data
        ]
        # Flatten the list if necessary and remove duplicates
        flat_list = []
        for item in resolved:
            if isinstance(item, list):
                for sub_item in item:
                    if sub_item not in flat_list:
                        flat_list.append(sub_item)
            else:
                if item not in flat_list:
                    flat_list.append(item)
        return flat_list
    elif isinstance(data, str):
        return resolve_placeholders(data, original_data)
    return data
