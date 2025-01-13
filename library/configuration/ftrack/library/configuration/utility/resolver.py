import glob
import os
import platform

import omegaconf
import platformdirs
import re
import socket
import time

from copy import deepcopy
from typing import Any
from omegaconf import OmegaConf, ListConfig, DictConfig
from pydantic.v1.utils import deep_update

from ..helper.enum import METADATA


def register_ft_resolvers() -> None:
    """
    Registers all default ftrack resolvers within the ft namespace.

    :return: None
    """
    register_runtime_cached()
    register_runtime_live()
    register_compose()
    register_exec()
    register_glob()
    register_join()
    register_key()
    register_lower()
    register_regex()
    register_paths()
    register_zip()


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


def register_exec():
    def _exec(executables: list[str], *arguments: list[str]) -> ListConfig:
        """
        Execute the given executables with the given arguments.
        NOTE: The arguments list will be applied to all executables in the same way.
        This resolver is built to run the same type of executable with the same arguments.

        :param executables: A list of executables to run.
        :param arguments: A list of arguments to apply to the executables.
        :return:
        """
        import subprocess

        results = OmegaConf.create([])
        for executable in executables:
            result = subprocess.run(
                [executable, *arguments], capture_output=True, text=True
            )
            results.append(result.stdout.strip("\n"))
        return results

    OmegaConf.register_new_resolver(
        "ft.exec", lambda executable, *arguments: _exec(executable, *arguments)
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
    def _regex_search(value, pattern, default="") -> ListConfig:
        """
        Match all values that match the given regex pattern.

        :param value: The value to match against.
        :param pattern: The regex pattern for matching.
        :return: A ListConfig object containing all the matched values.
        """
        # TODO: handle case for non-list values
        if not isinstance(value, (ListConfig, list)):
            value = [value]

        matches = []
        for v in value:
            if re_result := re.search(pattern, str(v)):
                if groups := re_result.groups():
                    match = groups[0]
                else:
                    match = re_result[0]

                matches.append(match or default)

        return OmegaConf.create(matches)

    def _regex_sub(value, replacement, pattern) -> ListConfig:
        """
        Replace all values that match the given regex pattern with the given replacement.

        :param value: The value to match against.
        :param replacement: The replacement string.
        :param pattern: The regex pattern to match.
        :return: If a match is found we return the replaced value, otherwise we return an empty string.
        """
        if not isinstance(value, (ListConfig, list)):
            value = [value]

        matches = []
        for v in value:
            replaced = re.sub(pattern, str(replacement), str(v))
            matches.append(replaced if replaced != v else "")

        return OmegaConf.create(matches)

    OmegaConf.register_new_resolver(
        "ft.regex.search",
        lambda value, pattern, default="": _regex_search(value, pattern, default),
    )
    OmegaConf.register_new_resolver(
        "ft.regex.sub",
        lambda value, replacement, pattern: _regex_sub(value, replacement, pattern),
    )


def register_lower():
    def _lower(value: str) -> str:
        """
        Lowercases the given value.

        :param value: The value to lowercase.
        :return: Lowercased string/value.
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
            # We need to create a copy of the reference to ensure we'll only remove the metadata
            # key from the final composed configuration keys, but retain it for the original source key.
            reference_duplicate = deepcopy(reference)
            if reference.get(METADATA.ROOT.value, {}).get(METADATA.DELETE.value, False):
                # Delete the metadata key from this reference so it won't show up in the
                # final composed key or in the metadata.
                del reference_duplicate[METADATA.ROOT.value]
            config = deep_update(config, reference_duplicate)

        return config

    OmegaConf.register_new_resolver(
        "ft.compose",
        lambda *references, _node_, _root_: _compose(
            references, _node_=_node_, _root_=_root_
        ),
    )


def register_zip():
    def _zip_dict(reference: DictConfig) -> DictConfig:
        """
        Will create a new list of dictionaries by zipping the values of the given reference dictionary.

        :param reference: The root of the input dictionary.
        :return: The list of dictionaries created by zipping the values of the input dictionary.
        """
        config = deepcopy(reference)
        if METADATA.ROOT.value in config:
            del config[METADATA.ROOT.value]

        zipped_lists = zip(*config.values())
        result = [dict(zip(config.keys(), values)) for values in zipped_lists]
        zipped_config = OmegaConf.create(result)
        return zipped_config

    def _zip_list(references: list[ListConfig]) -> ListConfig:
        """
        Will create a new list by zipping the values of the given references.

        :param references: The reference input lists to zip.
        :return: A new list created by zipping the values of the input lists.
        """
        references = list(references)
        max_len = max(len(reference) for reference in references)
        for idx, reference in enumerate(references):
            if not isinstance(reference, (list, ListConfig)):
                references[idx] = [reference] * max_len
        config = OmegaConf.create(list(zip(*references)))
        return config

    OmegaConf.register_new_resolver(
        "ft.zip.list", lambda *references: _zip_list(references)
    )
    OmegaConf.register_new_resolver("ft.zip.dict", lambda key: _zip_dict(key))


def register_join():
    def _join(references: list[ListConfig]) -> ListConfig:
        """
        Joins the given values into a single string. If the input is a list, it will join
        each item in the list and return a list with the joined items. This will work similarly
        to a `map` function.

        :param references: Input list of references to join.
        :return: A list with joined values.
        """
        config = OmegaConf.create([])
        for reference in references:
            config.append("_".join(reference))
        return config

    OmegaConf.register_new_resolver("ft.join", lambda references: _join(references))


def register_key():
    def _key(level, *, _node_: omegaconf.AnyNode) -> str:
        """
        Get the name of the key at the given parent level.

        :param level: The levels to go up in the hierarchy from the current node.
        :param _node_: Implicitly provided node at the current level (provided by OmegaConf).
        :return: The name of the parent at the given level.
        """
        parent = _node_
        for i in range(level):
            parent = parent._parent
        return parent._key()

    OmegaConf.register_new_resolver(
        "ft.key", lambda level, *, _node_: _key(level, _node_=_node_)
    )
