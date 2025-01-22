# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import yaml
import logging


def parse_configuration(configuration_file):
    """Parse the configuration file."""
    with open(configuration_file, "r") as yaml_file:
        try:
            yaml_content = yaml.safe_load(yaml_file)
        except yaml.YAMLError as exc:
            # Log an error if the yaml file is invalid.
            logging.error(
                logging.error(
                    f"Invalid .yaml file\nFile: {configuration_file}\nError: {exc}"
                )
            )
            raise
    return yaml_content


def recursive_find_in_nested_dictionary(obj, conditions, path=None, results=None):
    """
    Recursively traverse a nested structure (dicts/lists),
    returning sub-dictionaries that match *all* key=value conditions.

    :param obj: The root object (dict, list, or scalar).
    :param conditions: Dict of {key: value} to match (all must match).
    :param path: Internal param for tracking where we are in the nested structure.
    :param results: Accumulator list for matches.
    :return: A list of tuples: (path, matching_dict)
             where 'path' is a tuple of keys/indices to locate the sub-dict.
    """
    if results is None:
        results = []
    if path is None:
        path = ()

    # If it's a dictionary, we can check if it matches the conditions
    # and then recurse into its values.
    if isinstance(obj, dict):
        # Check if ALL conditions match in this dictionary
        if all(obj.get(k) == v for k, v in conditions.items()):
            results.append((path, obj))

        # Recurse into each key-value
        for k, v in obj.items():
            recursive_find_in_nested_dictionary(v, conditions, path + (k,), results)

    # If it's a list, recurse into each item
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            recursive_find_in_nested_dictionary(item, conditions, path + (i,), results)

    # If it's neither dict nor list (e.g. a string/int/float), just return
    return results
