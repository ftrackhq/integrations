"""DCC-specific profiles for the ConnectLauncher.

Each profile defines how to launch a specific DCC application:
quit function, command-line flags, environment variable names,
and macOS .app bundle resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DCCProfile:
    """Launch configuration for a specific DCC application."""

    name: str
    """Short name used with ``--dcc-app`` (e.g. ``"maya"``)."""

    quit_fn: str
    """Python expression for the quit callback.
    Evaluated inside the DCC on the main thread."""

    command_flag: str
    """CLI flag for passing startup code (e.g. ``"-command"``)."""

    command_template: str
    """Template for wrapping startup code on the CLI.
    Must contain ``{code}`` placeholder."""

    script_path_env: str
    """DCC-specific env var for script/plugin paths
    (e.g. ``"MAYA_SCRIPT_PATH"``)."""

    version_env: str
    """Env var for the DCC version
    (e.g. ``"FTRACK_MAYA_VERSION"``)."""

    app_bundle_binary: Optional[str]
    """Relative path from .app bundle to the actual binary
    on macOS. E.g. ``"Contents/bin/maya"``.
    None means resolve via Info.plist."""


PROFILES: dict[str, DCCProfile] = {
    "maya": DCCProfile(
        name="maya",
        quit_fn=(
            "lambda: __import__('maya.cmds', "
            "fromlist=['cmds']).quit(force=True)"
        ),
        command_flag="-command",
        command_template='python("{code}")',
        script_path_env="MAYA_SCRIPT_PATH",
        version_env="FTRACK_MAYA_VERSION",
        app_bundle_binary="Contents/bin/maya",
    ),
}


def get_profile(name: str) -> DCCProfile:
    """Return the profile for *name*.

    Raises ``ValueError`` if the DCC is not supported.
    """
    profile = PROFILES.get(name)
    if profile is None:
        available = ", ".join(sorted(PROFILES))
        raise ValueError(
            f"Unknown DCC application: {name!r}. Supported: {available}"
        )
    return profile
