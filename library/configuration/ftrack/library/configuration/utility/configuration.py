"""
This module provides functionality to load, merge, resolve and save configuration files.
The utilities in this module are designed to work nicely together.
They are supposed to be run in sequence. For example:

>>> register_resolvers()
>>> config_files = get_configurations_from_entrypoint("connect.configuration")
>>> more_config_files = get_configurations_from_namespace("ftrack.library")
>>> all_config_files = config_files.union(more_config_files)

>>> composed_configuration = compose_configuration_from_configurations(config_files)
>>> resolved_configuration = resolve_configuration(composed_configuration)
>>> save_configuration_to_yaml(resolved_configuration, Path("resolved.yaml"))

TODO: be more effecient in the usage of deepcopy (can we reduce the usage?)
"""

import base64
import importlib
import itertools
import logging
import os
import pickle
import pkgutil
import re

from copy import deepcopy
from collections import defaultdict
from importlib.metadata import entry_points
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

from omegaconf import OmegaConf, DictConfig, ListConfig

from ..helper.spec import ConfigurationSpec
from ..helper.enum import METADATA


logging.basicConfig(level=logging.INFO)


def _get_files_from_path(path: Path, pattern=r".*\.(yml|yaml)$") -> list[Path]:
    """
    Get all files from a given path that match the given pattern.
    We will only return top level files, no recursion is done.

    :param path: The parent path to search for files.
    :param pattern: The regex pattern to apply to the filenames.
    :return: A list of paths to the files that match the pattern.
    """
    files = []
    for _file in os.listdir(path):
        if re.match(pattern, _file):
            full_path = path / _file
            files.append(full_path)
    return files


def get_configurations_from_namespace(
    namespace: str = "",
    module_name: str = "",
) -> set[ConfigurationSpec]:
    """
    Get all configuration files from a given namespace.
    We will not search recursively, only the top level of the given paths will be searched.

    :param namespace: The namespace within the available packages to search for configuration files.
    :param module_name: The name of the module within the package to search for configuration files.
    :return: A list of paths to the configuration files.
    """

    configuration_sources = []
    root_namespace_package: ModuleType = importlib.import_module(namespace)
    packages = pkgutil.walk_packages(
        root_namespace_package.__path__, prefix=root_namespace_package.__name__ + "."
    )

    for package in packages:
        module_spec = package.module_finder.find_spec(package.name)
        # check if this is a package (non-packages will have a submodule_search_locations attribute of None)
        if (
            module_spec.submodule_search_locations
            and module_spec.name.split(".")[-1] == module_name
        ):
            module_path = Path(module_spec.origin).parent
            for _file in _get_files_from_path(module_path):
                configuration_sources.append(
                    ConfigurationSpec(
                        loader="namespace",
                        loader_arguments={
                            "namespace": namespace,
                            "module_name": module_name,
                        },
                        package_name=package.name,
                        file_path=_file,
                    )
                )

    return set(configuration_sources)


def get_configurations_from_entrypoint(
    name: str = "connect.configuration",
) -> set[ConfigurationSpec]:
    """
    Get all configuration files from a given entrypoint.
    We will not search recursively, only the top level of the given paths will be searched.

    :param name: The name of the entry point to look for configuration files.
    :return: A list of paths to the configuration files.
    """
    configuration_sources = []
    for entrypoint in entry_points()[name]:
        # load the configuration entry point so we execute and initialise any custom resolvers
        configuration_package = entrypoint.load()

        module_path = Path(configuration_package.__file__).parent
        for _file in _get_files_from_path(module_path):
            configuration_sources.append(
                ConfigurationSpec(
                    loader="entrypoint",
                    loader_arguments={"name": name},
                    package_name=configuration_package.__name__,
                    file_path=_file,
                )
            )

    return set(configuration_sources)


def get_configurations_from_paths(
    paths: list[Path] = "connect.configuration",
) -> set[ConfigurationSpec]:
    """
    Get all configuration files from a given set of paths.
    We will not search recursively, only the top level of the given paths will be searched.

    :param paths: A set of parent paths to search for configuration files.
    :return: A list of paths to the configuration files.
    """
    configuration_sources = []
    for path in paths:
        for _file in _get_files_from_path(path):
            configuration_sources.append(
                ConfigurationSpec(
                    loader="path",
                    loader_arguments={"paths": paths},
                    package_name="",
                    file_path=_file,
                )
            )
    return set(configuration_sources)


def check_configurations_for_conflicts(
    configurations: set[ConfigurationSpec], root_keys: list[str]
) -> dict[str, list[str]]:
    """
    Will compare each pair of the provided, non-empty configurations with each other and returns
    a dictionary with conflicting configurations grouped by conflicting keys.

    :param configurations: The configurations specs to compare.
    :param root_keys: The root keys to compare.
    :return: dictionary with conflicting configurations grouped by conflicting keys
    """

    def _compare(lhs, rhs, root_key):
        conflicting_keys = []
        for key in lhs.get(root_key, []):
            if key in rhs.get(root_key, []):
                conflicting_keys.append(f"{root_key}.{key}")
        return conflicting_keys

    # create all possible combinations of two configurations to compare them against
    # each other for conflicts
    combinations_for_conflict_checking = list(itertools.combinations(configurations, 2))

    conflicts = defaultdict(list)
    for lhs, rhs in combinations_for_conflict_checking:
        for root_key in root_keys:
            if configuration_conflict_keys := _compare(
                lhs.configuration, rhs.configuration, root_key
            ):
                logging.error(
                    "Configurations with overlapping keys have been found. "
                    "Please make sure to explicitly set a resolution method and/or order.:"
                )
                logging.error(lhs)
                logging.error(rhs)
                logging.error(f"{configuration_conflict_keys}")
                for configuration_conflict_key in configuration_conflict_keys:
                    conflicts[configuration_conflict_key].extend([str(lhs), str(rhs)])
    # Make sure that the root level entries in conflicts are unique by a transient conversion to a set.
    conflicts = {
        key: _ordered_deduplication(_deterministic_ordering(value))
        for key, value in conflicts.items()
    }
    return conflicts


def _deterministic_ordering(items: Iterable[Any]) -> list[Any]:
    return list(sorted(items, key=lambda x: repr(x)))


def _ordered_deduplication(items: Iterable[Any]) -> list[Any]:
    deduplicated_items = []
    for item in items:
        if item not in deduplicated_items:
            deduplicated_items.append(item)
    return deduplicated_items


def create_metadata_from_configuration_specs(
    configurations: set[ConfigurationSpec], conflict_resolution_method: str = "warn"
) -> DictConfig:
    metadata_configuration = OmegaConf.create(
        {METADATA.ROOT.value: {METADATA.SOURCES.value: OmegaConf.create({})}}
    )

    # add the actual configuration
    # TODO: This should probably be already done and only loaded from the hexdump.
    for configuration in configurations:
        configuration.configuration = OmegaConf.load(configuration.file_path)

    # remove any empty configuration from the list
    non_empty_configurations = set([_ for _ in configurations if _.configuration])

    for configuration in _ordered_deduplication(
        _deterministic_ordering(non_empty_configurations)
    ):
        metadata_configuration[METADATA.ROOT.value][METADATA.SOURCES.value][
            str(configuration)
        ] = configuration.to_dict()

    return metadata_configuration


def get_configuration_keys_by_pattern(configuration: DictConfig, pattern: re.Pattern):
    def _recursive_walk(parent):
        matched_keys = []

        for idx, key in enumerate(parent):
            if isinstance(parent, (list, ListConfig)):
                key = idx
            node = parent._get_node(key)
            full_key = parent._get_full_key(key)
            if not node:
                # FIXME: A reference can currently not be obtained for weird keys like the ones
                #  we have in the metadata sources e.g. 'LOADER:namespace|PACKAGE:ftrack.library.configuration|PATH:runtime.yaml'
                continue
            if re.match(pattern, full_key):
                matched_keys.append(full_key)
            if isinstance(node, (list, dict, ListConfig, DictConfig)):
                matched_keys.extend(_recursive_walk(node))
        return matched_keys

    return _recursive_walk(configuration)


def get_metadata_from_configuration_file(filepath) -> DictConfig:
    configuration = OmegaConf.load(filepath)
    metadata_configuration = configuration["_metadata"]
    return metadata_configuration


def create_configuration_specs_from_metadata(
    metadata: DictConfig,
) -> set[ConfigurationSpec]:
    specs = set()
    for key, value in metadata[METADATA.SOURCES.value].items():
        specs.add(ConfigurationSpec.from_dict(value))
    return specs


def compose_configuration_from_configuration_specs(
    configurations: set[ConfigurationSpec],
) -> DictConfig:
    """
    Given a list of configuration file paths, load and merge them into a single configuration object.

    :param configurations: A list of Path objects pointing to the configuration files.
    :return: A DictConfig object containing the merged configuration.
    """

    # TODO: Maybe we already have the configuration as a hexdump and we should load it from there?
    # add the actual configuration
    for configuration in configurations:
        configuration.configuration = OmegaConf.load(configuration.file_path)

    merged_configuration = OmegaConf.create({})

    for configuration in _ordered_deduplication(
        _deterministic_ordering(configurations)
    ):
        logging.info(f"Merging configuration: {configuration}")
        merged_configuration = OmegaConf.merge(
            merged_configuration, configuration.configuration
        )
    return merged_configuration


def compose_conflict_keys_in_specific_order_onto_configuration(
    configuration: DictConfig, metadata: DictConfig, conflicts: DictConfig
) -> DictConfig:
    """
    Compose/merge conflicting keys from a conflict config onto a given configuration.
    Conflict data/keys will be merged in the order they are defined in the conflict data.
    The conflict data will be loaded from the hexdump in the metadata (it will NOT be loaded from disk).

    :param configuration: The base configuration to merge the conflicts  keys into.
    :param metadata: The metadata object that contains the source and hexdump of the actual configs.
    :param conflicts: This object contains the conflicts that need to be resolved and defines their order.
    :return: The original configuration file with the composed keys on top of it.
    """

    composed_configuration = deepcopy(configuration)
    sources = metadata["_metadata"]["sources"]
    conflicts = conflicts["conflicts"]
    for conflict_key, conflict_sources in conflicts.items():
        root_key, child_key = conflict_key.split(".")
        del composed_configuration[root_key][child_key]
        for conflict_source in conflict_sources:
            config = deserialize_configuration_from_base64_hex(
                sources[conflict_source][root_key]
            )
            to_update = OmegaConf.create(
                {
                    root_key: OmegaConf.masked_copy(
                        config[root_key],
                        child_key,
                    )
                }
            )
            composed_configuration = OmegaConf.merge(composed_configuration, to_update)

    return composed_configuration


# TODO: we should MAYBE not only take DictConfig, but also Listconfig into account
def resolve_configuration(configuration: DictConfig) -> DictConfig:
    """
    Resolves all interpolation keys and executes all resolvers in the given configuration object.
    We will also delete all keys that are marked for deletion after composition.
    Deleted keys are "moved" into the global _metadata key for later reference.

    :param configuration: The configuration object to resolve.
    :return: The resolved configuration object.
    """
    resolved_configuration = deepcopy(configuration)
    OmegaConf.resolve(resolved_configuration)
    return resolved_configuration


def remove_keys_marked_for_deletion_from_configuration(
    configuration: DictConfig,
) -> DictConfig:
    clean_configuration = deepcopy(configuration)
    # FIXME: Somehow we're not selecting the +launch and ++launch keys here.
    #  this is probably happening because we're removing these metadata keys during composition...
    #  we should probably not delete them from the original key though
    candidate_keys = get_configuration_keys_by_pattern(
        clean_configuration, r"^.*_metadata.marked_for_deletion"
    )
    chosen_keys = [
        key for key in candidate_keys if OmegaConf.select(configuration, key) is True
    ]
    # FIXME: This is a temporary workaround. Ideally the remove_keys_from_configuration functino should be
    #  able to handle this properly. This is currently used to get from foo.bar._metadata.marked_for_deletion
    #  to foo to be able to delete the child bar
    grandparent_keys = [
        ".".join(key.split(".")[:-2]) for key in chosen_keys if "." in key
    ]
    clean_configuration = remove_keys_by_full_key(clean_configuration, grandparent_keys)
    return clean_configuration


def remove_keys_by_pattern(configuration: DictConfig, pattern: str = "+") -> DictConfig:
    """
    Remove all keys from the configuration that match the given pattern.

    :param configuration: The configuration object to remove keys from.
    :param pattern: The pattern to match the keys against.
    :return: A cleaned up configuration object.
    """

    def _recursive_remove(root):
        keys_to_delete = []
        for key, value in root.items():
            if key.startswith(pattern):
                keys_to_delete.append(key)
                continue
            if isinstance(value, dict):
                _recursive_remove(value)
        for key in keys_to_delete:
            del root[key]

    clean_configuration = deepcopy(configuration)
    _recursive_remove(clean_configuration)
    return clean_configuration


def remove_keys_by_full_key(configuration: DictConfig, keys: list[str]) -> DictConfig:
    # TODO: get the highest level key and ignore lower level keys (alternativevely we could sort by depth)
    clean_configuration = deepcopy(configuration)
    for full_key in keys:
        # FIXME: a node can only be selected when the result is a Config object (not plain old data)
        node = OmegaConf.select(clean_configuration, full_key)
        if not node:
            continue
        key = node._key()
        parent = node._parent
        if parent is None:
            del node._root[key]
        else:
            del parent[key]
    return clean_configuration


def convert_configuration_to_dict(configuration: DictConfig) -> dict:
    """
    Resolves the given configuration object into a dictionary.
    This will not automatically resolve the configuration.

    :param configuration: The configuration object to resolve.
    :param resolve: Whether to resolve the configuration or not.
    :return: The resolved and possibly cleaned up configuration as a dictionary.
    """
    resolved_configuration = OmegaConf.to_container(configuration, resolve=False)
    return resolved_configuration


def save_configuration_to_yaml(configuration: DictConfig, path: Path) -> None:
    """
    Safely write the configuration to a yaml file.
    This will not automatically resolve the configuration.

    :param configuration: The configuration object to write.
    :param path: The path to write the configuration to.
    :return: None
    """
    OmegaConf.save(configuration, path)


# TODO: Test this functionality properly
def serialize_configuration_to_base64_hex(configuration: DictConfig) -> str:
    # Serialize the object to a pickle byte stream
    pickled_data = pickle.dumps(configuration)
    # Encode the byte stream to a base64 string
    base64_encoded = base64.b64encode(pickled_data).decode("utf-8")
    # Convert the base64 string to a hexdump
    hexdump = base64_encoded.encode("utf-8").hex()
    return hexdump


def deserialize_configuration_from_base64_hex(hexdump: str) -> DictConfig:
    # Convert the hexdump back to a base64 string
    base64_encoded = bytes.fromhex(hexdump).decode("utf-8")
    # Decode the base64 string to a pickle byte stream
    pickled_data = base64.b64decode(base64_encoded)
    # Deserialize the pickle byte stream to an object
    configuration = pickle.loads(pickled_data)
    return configuration
