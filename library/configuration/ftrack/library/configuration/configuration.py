# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

# TODO: Maybe the configurationspec can only be in one state at a time
#  it can not contain multiple states at the same time. This will ensure
#  that the configuration is always in a valid state.
#  We'll always clear all successive states when a previous state is changed.

import logging
import tempfile

from pathlib import Path
from typing import Self

from omegaconf import DictConfig

from .helper.spec import ConfigurationSpec
from .utility.configuration import (
    get_configurations_from_entrypoint,
    get_configurations_from_namespace,
    get_configurations_from_paths,
    get_configurations_from_metadata,
    get_metadata_from_configuration_specs,
    save_configuration_to_yaml,
    convert_configuration_to_dict,
    compose_configuration_from_configurations,
    resolve_configuration,
)

logging.basicConfig(level=logging.INFO)


class Configuration:
    def __init__(self):
        # TODO: at each stage, we should store the hash of the configuration to be able to check if it has changed
        self._specs: set[ConfigurationSpec] = set()
        self._specs_hash: str = ""  # Generated from specs
        self._metadata: DictConfig = DictConfig({})
        self._metadata_hash: str = ""  # Generated from specs and metadata
        self._composed: DictConfig = DictConfig({})
        self._composed_hash: str = ""  # Generated from specs, metadata and composed
        self._resolved: DictConfig = DictConfig({})
        self._resolved_hash: str = (
            ""  # Generated from specs, metdata, composed and resolved
        )

    @property
    def metadata(self) -> DictConfig:
        return self._metadata

    @property
    def metadata_hash(self) -> str:
        return self._metadata_hash

    @property
    def composed(self) -> DictConfig:
        return self._composed

    @property
    def composed_hash(self) -> hash:
        return self._composed_hash

    @property
    def resolved(self) -> DictConfig:
        return self._resolved

    @property
    def resolved_hash(self) -> hash:
        return self._resolved_hash

    def load_from_entrypoint(self, entrypoint: str) -> Self:
        self._specs = self._specs.union(get_configurations_from_entrypoint(entrypoint))
        self._generate_metadata_from_specs()
        return self

    def load_from_namespace(self, namespace: str, module_name: str) -> Self:
        self._specs = self._specs.union(
            get_configurations_from_namespace(namespace, module_name)
        )
        self._generate_metadata_from_specs()
        return self

    def load_from_paths(self, paths: list[Path]) -> Self:
        self._specs = self._specs.union(get_configurations_from_paths(paths))
        self._generate_metadata_from_specs()
        return self

    def load_from_metadata(self, metadata: DictConfig) -> Self:
        self._specs = self._specs.union(get_configurations_from_metadata(metadata))
        return self

    def _generate_metadata_from_specs(self) -> Self:
        self._metadata = get_metadata_from_configuration_specs(self._specs)
        return self

    # TODO: validate if the specs and metadata are in alignment to each other
    def validate(self) -> bool:
        raise NotImplementedError

    def clear(self) -> Self:
        self._specs = set()
        self._specs_hash = ""
        self._metadata = DictConfig({})
        self._metadata_hash = ""
        self._composed = DictConfig({})
        self._composed_hash = ""
        self._resolved = DictConfig({})
        self._resolved_hash = ""
        return self

    def compose(self, ignore_validation=False) -> Self:
        self._composed = compose_configuration_from_configurations(self._specs)
        return self

    def resolve(self) -> Self:
        self._resolved = resolve_configuration(self._composed)
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
        save_configuration_to_yaml(self._composed, folder / "composed.yaml")
        save_configuration_to_yaml(self._metadata, folder / "resolved.yaml")

        return True
