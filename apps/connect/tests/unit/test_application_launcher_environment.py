# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Unit tests for the frozen-Qt environment scrub in the launcher.

Covers the pure helpers ftrack Connect uses to keep its own bundled Qt
paths (injected by PyInstaller's PySide6 runtime hook when Connect runs
frozen) out of the environment handed to launched DCCs. See
docs/specs/2026-07-15-qt-env-leak-frozen-connect-design.md.

The helpers take their bundle roots as arguments, so these run
everywhere without a frozen build.
"""

import os

import pytest

from ftrack_connect.application_launcher import (
    FROZEN_QT_ENVIRONMENT_VARIABLES,
    restore_loader_library_path,
    strip_frozen_qt_environment,
)

SEP = os.pathsep


def join(*paths):
    return SEP.join(paths)


def test_bundle_only_value_removes_var():
    """A var holding only a bundle entry is dropped entirely."""
    root = os.path.normpath("/opt/connect/_internal")
    env = {"QT_PLUGIN_PATH": os.path.join(root, "PySide6", "plugins")}

    strip_frozen_qt_environment(env, [root])

    assert "QT_PLUGIN_PATH" not in env


def test_mixed_keeps_studio_entries_in_order():
    """Foreign entries survive, in their original order; bundle drops."""
    root = os.path.normpath("/opt/connect/_internal")
    studio_a = os.path.normpath("/studio/qt/a/plugins")
    studio_b = os.path.normpath("/studio/qt/b/plugins")
    bundle = os.path.join(root, "PySide6", "plugins")
    env = {"QT_PLUGIN_PATH": join(studio_a, bundle, studio_b)}

    strip_frozen_qt_environment(env, [root])

    assert env["QT_PLUGIN_PATH"] == join(studio_a, studio_b)


def test_studio_only_untouched():
    """Nothing under a bundle root -> the var is left exactly as-is."""
    root = os.path.normpath("/opt/connect/_internal")
    original = join(
        os.path.normpath("/studio/qt/a"), os.path.normpath("/studio/qt/b")
    )
    env = {"QML2_IMPORT_PATH": original}

    strip_frozen_qt_environment(env, [root])

    assert env["QML2_IMPORT_PATH"] == original


def test_entry_equal_to_root_removed():
    """An entry that *is* the root (no trailing path) is a bundle entry."""
    root = os.path.normpath("/opt/connect/_internal")
    env = {"QT_PLUGIN_PATH": root}

    strip_frozen_qt_environment(env, [root])

    assert "QT_PLUGIN_PATH" not in env


def test_prefix_collision_sibling_survives():
    """A sibling dir sharing the root's textual prefix is not stripped."""
    root = os.path.normpath("/opt/connect_internal")
    sibling = os.path.normpath("/opt/connect_internal_other/plugins")
    env = {"QT_PLUGIN_PATH": sibling}

    strip_frozen_qt_environment(env, [root])

    assert env["QT_PLUGIN_PATH"] == sibling


def test_windows_case_and_slash_normalization():
    """Windows: case-insensitive, slash-insensitive matching."""
    if os.sep != "\\":
        pytest.skip("Windows path semantics")
    root = r"C:\Program Files\ftrack Connect\_internal"
    # Different case + forward slashes must still match the root.
    bundle = "c:/program files/ftrack connect/_internal/PySide6/plugins"
    studio = r"D:\studio\qt\plugins"
    env = {"QT_PLUGIN_PATH": join(bundle, studio)}

    strip_frozen_qt_environment(env, [root])

    assert env["QT_PLUGIN_PATH"] == studio


def test_macos_two_roots_strips_frameworks_and_resources():
    """macOS: both the _MEIPASS (Frameworks) and .app-root QML entries go."""
    app_root = os.path.normpath("/Applications/Ftrack Connect.app")
    meipass = os.path.join(app_root, "Contents", "Frameworks")
    frameworks_qml = os.path.join(meipass, "PySide6", "Qt", "qml")
    resources_qml = os.path.join(app_root, "Contents", "Resources", "qml")
    studio = os.path.normpath("/studio/qml")
    env = {"QML2_IMPORT_PATH": join(frameworks_qml, resources_qml, studio)}

    # Roots as get_frozen_bundle_roots would return them on macOS.
    strip_frozen_qt_environment(env, [meipass, app_root])

    assert env["QML2_IMPORT_PATH"] == studio


def test_path_only_loses_meipass_entry():
    """PATH keeps every entry except the bundle (_MEIPASS) one."""
    root = os.path.normpath("/opt/connect/_internal")
    system_a = os.path.normpath("/usr/bin")
    system_b = os.path.normpath("/bin")
    env = {"PATH": join(system_a, root, system_b)}

    strip_frozen_qt_environment(env, [root])

    assert env["PATH"] == join(system_a, system_b)


def test_empty_roots_is_noop():
    """No bundle roots (not frozen) -> the environment is untouched."""
    original = os.path.normpath("/opt/connect/_internal/PySide6/plugins")
    env = {"QT_PLUGIN_PATH": original, "PATH": os.path.normpath("/usr/bin")}

    strip_frozen_qt_environment(env, [])

    assert env == {
        "QT_PLUGIN_PATH": original,
        "PATH": os.path.normpath("/usr/bin"),
    }


def test_all_frozen_vars_covered():
    """Every declared frozen Qt var is scrubbed when bundle-owned."""
    root = os.path.normpath("/opt/connect/_internal")
    env = {
        key: os.path.join(root, key.lower())
        for key in FROZEN_QT_ENVIRONMENT_VARIABLES
    }

    strip_frozen_qt_environment(env, [root])

    assert env == {}


def test_restore_loader_library_path_with_orig():
    """LD_LIBRARY_PATH is restored from the bootloader's _ORIG copy."""
    env = {
        "LD_LIBRARY_PATH": "/opt/connect/_internal",
        "LD_LIBRARY_PATH_ORIG": "/studio/libs",
    }

    restore_loader_library_path(env)

    assert env == {"LD_LIBRARY_PATH": "/studio/libs"}


def test_restore_loader_library_path_without_orig():
    """No _ORIG (caller had none) -> LD_LIBRARY_PATH is dropped."""
    env = {"LD_LIBRARY_PATH": "/opt/connect/_internal"}

    restore_loader_library_path(env)

    assert env == {}


def test_restore_loader_library_path_empty_orig_preserved():
    """An empty original is restored verbatim (distinct from absent)."""
    env = {
        "LD_LIBRARY_PATH": "/opt/connect/_internal",
        "LD_LIBRARY_PATH_ORIG": "",
    }

    restore_loader_library_path(env)

    assert env == {"LD_LIBRARY_PATH": ""}
