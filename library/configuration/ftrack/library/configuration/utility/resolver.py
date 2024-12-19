import glob
import os
import platform
import platformdirs
import re
import socket
import time

from typing import Any
from omegaconf import OmegaConf, ListConfig, DictConfig
from pydantic.v1.utils import deep_update

from ..helper.metadata import METADATA


def register_ft_resolvers() -> None:
    """
    Registers all default ftrack resolvers.

    :return: None
    """
    register_runtime_cached()
    register_runtime_live()
    register_compose()
    register_glob()
    register_lower()
    register_regex()
    register_paths()


def register_runtime_cached():
    # TODO: Filling in the runtime args like this is up for discussion as we could also handle it differently.
    # These will be lazily evaluated when the config is accessed
    def _runtime_cached(value: str):
        # All of these will be cached and only evaluated once.
        match value:
            case "architecture":
                return platform.architecture()[0]
            case "platform":
                return platform.system()
            case "username":
                return os.getlogin()
            case "hostname":
                return socket.gethostname()
            case "python_version":
                return platform.python_version()
            case "time":
                return time.time()
            case "time":
                return time.time()
            case _:
                return "None"

    OmegaConf.register_new_resolver(
        "ft.runtime.cached", lambda key: _runtime_cached(key), use_cache=True
    )


def register_runtime_live():
    def _runtime_live(value: str):
        # All of these will be evaluated every time the config value is accessed.
        match value:
            case "time":
                return time.time()
            case _:
                return "None"

    OmegaConf.register_new_resolver("ft.runtime.live", lambda key: _runtime_live(key))


def register_paths():
    def _paths(path_type: str, scope: str) -> str:
        path_getter_method_name = f"{scope}_{path_type}_path"
        supported_path_types = [
            _.split("_")[1] for _ in dir(platformdirs) if re.match(r"user_.+_path", _)
        ]
        if path_type not in supported_path_types:
            raise ValueError(
                f"Path type {path_type} cannot be resolved. Supported path types are {supported_path_types}"
            )

        path_getter_method = getattr(platformdirs, path_getter_method_name)
        assert path_getter_method
        return path_getter_method("ftrack-connect").as_posix()

    OmegaConf.register_new_resolver(
        "ft.paths",
        lambda path_type, scope="user": _paths(path_type, scope),
        use_cache=True,
    )


def register_glob():
    def _glob(value: str) -> ListConfig:
        """
        Match all paths that match the given glob pattern.

        :param value:
        :return: A ListConfig object containing all the matched paths.
        """
        matches = glob.glob(value)
        return OmegaConf.create(matches)

    OmegaConf.register_new_resolver("ft.glob", lambda key: _glob(key))


def register_regex():
    def _regex(value, pattern) -> ListConfig:
        """
        Match all values that match the given regex pattern.

        :param value: The value to match against.
        :param pattern: The regex pattern for matching.
        :return: A ListConfig object containing all the matched values.
        """
        if not isinstance(value, (ListConfig, list)):
            value = [value]

        matches = []
        for v in value:
            if match := re.search(pattern, str(v)):
                matches.append(match[0])

        return OmegaConf.create(matches)

    OmegaConf.register_new_resolver(
        "ft.regex", lambda value, pattern: _regex(value, pattern)
    )


def register_lower():
    def _lower(value: str) -> str:
        """
        Lowercases the given value.
        :param key:
        :return:
        """
        return value.lower()

    OmegaConf.register_new_resolver("ft.lower", lambda key: _lower(key))


def register_compose():
    def _compose(references: list[Any], *, _node_, _root_) -> DictConfig:
        """
        Composes the given references into a single configuration object.

        Example:
        launch: "${ft.compose: ${configuration.maya-default.launch}, ${.my_override}, ${.my_other_override}}"
        my_override::
          delete_after_compose: True
          discovery-hook: "my_override"
        my_other_override:
          windows: "C:\*"

        The above example will compose configuration.maya-default.launch, my_override and my_other_override.
        The composition is done in order and sparsely, meaning we'll match and add/replace the lowest possible
        node in the hierarchy.
        Additionally, we will delete the my_override key after composing it due to it having the delete_after_compose
        flag set to True.

        :param references: A List of references.
        :param _node_: The implicitly provided current node.
        :param _root_: The implicitly provided root node of the configuration.
        :return: A DictConfig object containing the composed configuration.
        """
        config = OmegaConf.create({})
        for reference in references:
            full_reference_key = reference._parent._get_full_key(reference._key())
            if reference.get(METADATA.ROOT.value, {}).get(METADATA.ROOT.value, False):
                # Delete the metadata key from this reference so it won't show up in the
                # final composed key or in the metadata.
                del reference[METADATA.ROOT.value]
                _root_[METADATA.ROOT.value][METADATA.DELETE.value].append(
                    full_reference_key
                )
            config = deep_update(config, reference)

        return config

    OmegaConf.register_new_resolver(
        "ft.compose",
        lambda *references, _node_, _root_: _compose(
            references, _node_=_node_, _root_=_root_
        ),
    )
