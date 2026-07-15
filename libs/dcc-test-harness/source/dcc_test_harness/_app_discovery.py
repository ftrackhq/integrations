"""Discover DCC executables from ftrack-connect YAML launch configs.

Simplified reimplementation of ``ApplicationStore._search_filesystem``
from ``ftrack_connect.application_launcher``.  No ftrack dependencies
required — only PyYAML for reading the config files.
"""

from __future__ import annotations

import logging
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

#: Default regex matching version numbers in file paths.
#: Matches the last group of digits (optionally with dots).
DEFAULT_VERSION_EXPRESSION = re.compile(r"(?P<version>\d[\d.vabc]*?)[^\d]*$")

_PLATFORM_KEY = {
    "Darwin": "darwin",
    "Linux": "linux",
    "Windows": "windows",
}


@dataclass
class DiscoveredApp:
    """A DCC executable found on the filesystem."""

    path: str
    version: str


def load_launch_config(yaml_path: Path) -> dict:
    """Read a ftrack-connect launch YAML config."""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def discover_executable(
    launch_config: dict,
    version: Optional[str] = None,
) -> DiscoveredApp:
    """Find the DCC executable described by *launch_config*.

    Reads the ``search_path`` section for the current platform
    and scans the filesystem.

    Args:
        launch_config: Parsed YAML launch config dict.
        version: If set, select the version that starts with
            this string (e.g. ``"2025"``).  If ``None``, the
            newest discovered version is returned.

    Raises ``FileNotFoundError`` if no executable is found.
    """
    current_os = _PLATFORM_KEY.get(platform.system())
    if current_os is None:
        raise FileNotFoundError(f"Unsupported platform: {platform.system()}")

    search = launch_config.get("search_path", {})
    platform_search = search.get(current_os)
    if platform_search is None:
        raise FileNotFoundError(
            f"No search_path for platform {current_os!r} in launch config"
        )

    prefix = platform_search["prefix"]
    expression = platform_search["expression"]
    version_expression = platform_search.get("version_expression")

    results = search_filesystem(prefix, expression, version_expression)

    label = launch_config.get("label", "DCC")

    if not results:
        raise FileNotFoundError(
            f"Could not find {label} on this system. "
            f"Searched: {prefix + expression}. "
            f"Use --dcc-executable to specify the path."
        )

    logger.info(
        "Discovered %s versions: %s",
        label,
        ", ".join(f"{r.version} ({r.path})" for r in results),
    )

    if version is not None:
        matches = [r for r in results if r.version.startswith(version)]
        if not matches:
            available = ", ".join(r.version for r in results)
            raise FileNotFoundError(
                f"No {label} version matching "
                f"{version!r} found. "
                f"Available: {available}"
            )
        return matches[0]

    return results[0]


def search_filesystem(
    prefix: list[str],
    expression: list[str],
    version_expression: Optional[str] = None,
) -> list[DiscoveredApp]:
    """Walk the filesystem matching regex patterns.

    *prefix* and *expression* are concatenated.  The first
    element becomes the walk root (must exist on disk).
    Remaining elements become regexes, one per directory level.

    Returns discovered apps sorted by version descending.
    """
    pieces = list(prefix) + list(expression)
    root = pieces[0]

    # On Windows, "C:" means current dir — normalise to "C:\\"
    if platform.system() == "Windows" and root.endswith(":"):
        root += "\\"

    if not os.path.exists(root):
        return []

    patterns = [re.compile(p) for p in pieces[1:]]
    pattern_count = len(patterns)

    if version_expression:
        ver_re = re.compile(version_expression)
    else:
        ver_re = DEFAULT_VERSION_EXPRESSION

    results: list[DiscoveredApp] = []

    for dirpath, dirnames, filenames in os.walk(
        root, topdown=True, followlinks=True
    ):
        # Absolute separator count gives the current level,
        # matching the connect implementation.
        level = dirpath.rstrip(os.sep).count(os.sep)

        if level >= pattern_count:
            dirnames.clear()
            continue

        pattern = patterns[level]

        if level < pattern_count - 1:
            # Prune non-matching directories.
            dirnames[:] = [d for d in dirnames if pattern.match(d)]
        else:
            # Final level: match executables and .app bundles.
            for entry in dirnames + filenames:
                if pattern.match(entry):
                    full_path = os.path.join(dirpath, entry)
                    ver_match = ver_re.search(full_path)
                    version = ver_match.group("version") if ver_match else "0"
                    results.append(
                        DiscoveredApp(path=full_path, version=version)
                    )
            # Don't descend further.
            dirnames.clear()

    results.sort(key=lambda a: a.version, reverse=True)
    return results
