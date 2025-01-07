import base64
import pickle

from typing import Self
from pathlib import Path
from omegaconf import OmegaConf, DictConfig


class ConfigurationSpec:
    def __init__(
        self,
        loader: str = "",
        loader_arguments: dict = None,
        package_name: str = "",
        file_path: Path = "",
        configuration: DictConfig = None,
    ):
        self.loader = loader
        self.loader_arguments = loader_arguments or {}
        self.package_name = package_name
        self.file_path = file_path
        # We're setting the default value here instead of the argument list
        # to avoid having a reference type as the default.
        self.configuration = configuration or OmegaConf.create({})
        self.order = -1

    def __str__(self):
        if self.package_name:
            return f"LOADER-{self.loader}-PACKAGE-{self.package_name}-PATH-{self.file_path.name}"
        else:
            return f"LOADER-{self.loader}-PATH-{self.file_path}"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.file_path)

    # We implement __eq__ to make sure that comparison is only done based on our criteria
    # This is important to avoid having the same spec multiple times in a set.
    # Python will otherwise use the hash for a quick comparison and then fall back to the __eq__method
    # for a more thorough check. If we don't implement this ourselves, we will end up with specs that
    # should be considered equal but are not.
    def __eq__(self, other):
        return hash(self) == hash(other)

    def config_as_base64(self) -> str:
        # Serialize the object to a pickle byte stream
        pickled_data = pickle.dumps(self.configuration)
        # Encode the byte stream to a base64 string
        base64_encoded = base64.b64encode(pickled_data).decode("utf-8")
        # Convert the base64 string to a hexdump
        hexdump = base64_encoded.encode("utf-8").hex()
        return hexdump

    @staticmethod
    def config_from_base64(hexdump: str) -> DictConfig:
        # Convert the hexdump back to a base64 string
        base64_encoded = bytes.fromhex(hexdump).decode("utf-8")
        # Decode the base64 string to a pickle byte stream
        pickled_data = base64.b64decode(base64_encoded)
        # Deserialize the pickle byte stream to an object
        configuration = pickle.loads(pickled_data)
        return configuration

    def to_dict(self) -> dict:
        return {
            "loader": self.loader,
            "loader_arguments": self.loader_arguments,
            "package_name": self.package_name,
            "file_path": str(self.file_path),
            "configuration": self.config_as_base64(),
        }

    @staticmethod
    def from_dict(state: dict) -> Self:
        spec = ConfigurationSpec()
        spec.loader = state["loader"]
        spec.loader_arguments = state["loader_arguments"]
        spec.package_name = state["package_name"]
        spec.file_path = Path(state["file_path"])
        spec.configuration = spec.config_from_base64(state["configuration"])
        return spec
