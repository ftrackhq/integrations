from pathlib import Path
from omegaconf import OmegaConf, DictConfig


class ConfigurationSpec:
    def __init__(
        self,
        package_name: str = "",
        file_path: Path = "",
        configuration: DictConfig = OmegaConf.create({}),
    ):
        self.package_name = package_name
        self.file_path = file_path
        self.configuration = configuration

    # TODO: This should probably just be the string representation
    @property
    def identifier(self):
        if self.package_name and self.file_path:
            return f"{self.package_name}:{self.file_path.name}"
        elif self.file_path:
            return self.file_path
        else:
            return None

    def __hash__(self):
        return hash(self.file_path)
