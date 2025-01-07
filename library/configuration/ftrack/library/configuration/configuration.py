# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

# TODO: make sure that the sources in the metadata (especially for conflicts) are always in the same order
# TODO: Maybe the configuration can only be in one state at a time
#  it can not contain multiple states at the same time. This will ensure
#  that the configuration is always in a valid state.
#  We'll always clear all successive states when a previous state is changed.

import logging
import tempfile

from pathlib import Path
from typing import Self

from omegaconf import OmegaConf, DictConfig

from .helper.types import ConfigurationSpec
from .utility.configuration import (
    get_configuration_specs_from_entrypoint,
    get_configuration_specs_from_namespace,
    get_configuration_specs_from_paths,
    get_conflicts_from_configuration_specs,
    get_configuration_keys_by_pattern,
    create_metadata_from_configuration_specs,
    create_configuration_specs_from_metadata,
    save_configuration_to_yaml,
    convert_configuration_to_dict,
    compose_conflict_keys_in_specific_order_onto_configuration,
    compose_configuration_from_configuration_specs,
    resolve_configuration,
    remove_keys_marked_for_deletion,
    remove_keys_by_full_key,
)

logging.basicConfig(level=logging.INFO)


class Configuration:
    """
    This class wraps the configuration process and provides a simple interface to load, compose and resolve configurations.
    Where feasible, it exposes a fluent interface to chain the configuration steps e.g.
    Configuration().load_from_entrypoint("connect.configuration").compose().resolve().dump("/tmp/configurations")
    """

    def __init__(self):
        # TODO: when we generate the metadata from the specs, we'll always stop on conflicts
        #  when metadata is provided by the user, we'll use the CONFLICT_HANDLING
        self._specs: set[ConfigurationSpec] = set()
        self._metadata: DictConfig = OmegaConf.create({})
        self._conflicts: DictConfig = OmegaConf.create({})
        self._composed: DictConfig = OmegaConf.create({})
        self._resolved: DictConfig = OmegaConf.create({})

    @property
    def metadata(self) -> DictConfig:
        return self._metadata

    @property
    def conflicts(self) -> DictConfig:
        return self._conflicts

    @property
    def composed(self) -> DictConfig:
        return self._composed

    @property
    def resolved(self) -> DictConfig:
        return self._resolved

    def load_from_entrypoint(self, entrypoint: str) -> Self:
        self._specs = self._specs.union(
            get_configuration_specs_from_entrypoint(entrypoint)
        )
        self._generate_metadata_from_specs()
        return self

    def load_from_namespace(self, namespace: str, module_name: str) -> Self:
        self._specs = self._specs.union(
            get_configuration_specs_from_namespace(namespace, module_name)
        )
        self._generate_metadata_from_specs()
        return self

    def load_from_paths(self, paths: list[Path]) -> Self:
        self._specs = self._specs.union(get_configuration_specs_from_paths(paths))
        self._generate_metadata_from_specs()
        return self

    def load_from_metadata_file(self, path: Path) -> Self:
        loaded_metadata = OmegaConf.load(path)
        specs = create_configuration_specs_from_metadata(loaded_metadata["_metadata"])
        computed_metadata = create_metadata_from_configuration_specs(specs)
        # TODO: Be more specific in the handling of this case.
        assert (
            loaded_metadata == computed_metadata
        ), "The loaded metadata does not match the generated metadata."
        # TODO: We might want to avoid storing the specs and compute everything directly
        #  on-the-fly from the metadata.
        self._specs = specs
        self._metadata = computed_metadata
        return self

    def _generate_metadata_from_specs(self) -> Self:
        self._metadata = create_metadata_from_configuration_specs(self._specs)
        return self

    def _check_configuration_specs_for_conflicts(self) -> Self:
        self._conflicts["conflicts"] = get_conflicts_from_configuration_specs(
            self._specs, ["configuration"]
        )
        return self

    def clear(self) -> Self:
        self._specs = set()
        self._metadata = OmegaConf.create({})
        self._composed = OmegaConf.create({})
        self._resolved = OmegaConf.create({})
        return self

    def compose(self, conflict_resolution_file: Path) -> Self:
        self._check_configuration_specs_for_conflicts()
        specs = create_configuration_specs_from_metadata(self._metadata["_metadata"])
        self._composed = compose_configuration_from_configuration_specs(specs)
        if self._conflicts and not conflict_resolution_file:
            raise ValueError("Conflicts detected in the configuration.")
        # TODO: We're already creating the specs when loading the metadata from a file.
        #  We should be more consistent and either ONLY use the metadata, or ONLY use the specs.
        else:
            conflicts = OmegaConf.load(conflict_resolution_file)
            self._composed = compose_conflict_keys_in_specific_order_onto_configuration(
                self._composed, self._metadata, conflicts
            )
        return self

    def resolve(self, clean=True) -> Self:
        self._resolved = resolve_configuration(self._composed)
        if clean:
            self._resolved = remove_keys_marked_for_deletion(self._resolved)
            metadata_keys = get_configuration_keys_by_pattern(
                self._resolved, r"^.*_metadata$"
            )
            self._resolved = remove_keys_by_full_key(self._resolved, metadata_keys)
        return self

    @staticmethod
    def as_dict(configuration: DictConfig) -> dict:
        return convert_configuration_to_dict(configuration)

    @staticmethod
    def to_yaml(configuration, filepath: Path) -> None:
        save_configuration_to_yaml(configuration, filepath)

    def dump(self, folder: Path) -> bool:
        """
        Dumps all configuration steps to the given folder.

        :param folder: The folder to dump the configurations to.
        :return: Success
        """
        # First check if we have a valid folder and we can write to it.
        folder = Path(folder)
        try:
            with tempfile.TemporaryFile(dir=folder):
                pass
        except Exception:
            logging.error(
                f"{folder} is not a valid folder, can't be written to or does not exist."
            )
            return False

        save_configuration_to_yaml(self._metadata, folder / "metadata.yaml")
        save_configuration_to_yaml(self._conflicts, folder / "conflicts.yaml")
        save_configuration_to_yaml(self._composed, folder / "composed.yaml")
        save_configuration_to_yaml(self._resolved, folder / "resolved.yaml")

        return True
