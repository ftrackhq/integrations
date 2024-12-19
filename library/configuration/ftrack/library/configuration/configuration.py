# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

from pathlib import Path
from omegaconf import DictConfig

from .helper.spec import ConfigurationSpec
from .utility.configuration import (
    get_configurations_from_entrypoint,
    get_configurations_from_namespace,
    get_configurations_from_paths,
    create_metadata_from_configuration_specs,
    save_configuration_to_yaml,
    convert_configuration_to_dict,
)

logging.basicConfig(level=logging.INFO)


class Configuration:
    def __init__(self):
        self._specs: set[ConfigurationSpec] = set()
        self._metadata: DictConfig = DictConfig({})
        self._composed: DictConfig = DictConfig({})
        self._resolved: DictConfig = DictConfig({})

    @property
    def metadata(self) -> DictConfig:
        return self._metadata

    @property
    def specs(self) -> set[ConfigurationSpec]:
        return self._specs

    @property
    def composed(self) -> DictConfig:
        return self._composed

    @property
    def resolved(self) -> DictConfig:
        return self._resolved

    def load_from_entrypoint(self, entrypoint: str) -> None:
        self._specs.union(get_configurations_from_entrypoint(entrypoint))

    def load_from_namespace(self, namespace: str) -> None:
        self._specs.union(get_configurations_from_namespace(namespace))

    def load_from_paths(self, paths: list[Path]) -> None:
        self._specs.union(get_configurations_from_paths(paths))

    def metadata_from_specs(self) -> None:
        self._metadata = create_metadata_from_configuration_specs(self._specs)

    def compose(self) -> None:
        raise NotImplementedError

    def resolve(self) -> None:
        raise NotImplementedError

    def check(self) -> None:
        raise NotImplementedError

    @staticmethod
    def as_dict(configuration: DictConfig) -> dict:
        return convert_configuration_to_dict(configuration)

    @staticmethod
    def to_yaml(configuration, filepath: Path) -> None:
        save_configuration_to_yaml(configuration, filepath)
