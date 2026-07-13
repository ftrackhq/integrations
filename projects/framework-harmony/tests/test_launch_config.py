# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Unit tests for the Harmony launch config search expressions.

Pure config tests - no Harmony install or ftrack credentials needed.

Regression: the darwin app expression used to be ``Harmony \\d[\\w.]
<Edition>.app``, which matches exactly two version characters - so
"Harmony 27 Premium.app" was discovered but "Harmony 25.2 Premium.app"
never was, and the version was missing from the Connect launcher menu.
"""

import re
from pathlib import Path

import pytest

from dcc_test_harness._app_discovery import load_launch_config

LAUNCH_DIR = Path(__file__).resolve().parent.parent / "extensions" / "launch"

EDITIONS = ["premium", "advanced", "essentials"]

# Single- and two-component marketing versions Connect must discover.
VERSIONS = ["22", "27", "25.2"]


def _darwin_expressions(edition):
    config = load_launch_config(LAUNCH_DIR / f"harmony-launch-{edition}.yaml")
    folder_expr, app_expr = config["search_path"]["darwin"]["expression"]
    return re.compile(folder_expr), re.compile(app_expr)


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("edition", EDITIONS)
def test_darwin_expression_discovers_version(edition, version):
    """Both path levels must match, as Connect re.match()es each level."""
    folder_re, app_re = _darwin_expressions(edition)
    title = edition.capitalize()

    assert folder_re.match(f"Toon Boom Harmony {version} {title}")
    assert app_re.match(f"Harmony {version} {title}.app")


@pytest.mark.parametrize("edition", EDITIONS)
def test_darwin_expression_is_edition_specific(edition):
    folder_re, app_re = _darwin_expressions(edition)
    other = "Advanced" if edition == "premium" else "Premium"

    assert not app_re.match(f"Harmony 27 {other}.app")
    assert not folder_re.match("Toon Boom Storyboard Pro 27")


@pytest.mark.parametrize("edition", EDITIONS)
def test_windows_expression_discovers_minor_version(edition):
    config = load_launch_config(LAUNCH_DIR / f"harmony-launch-{edition}.yaml")
    version_folder_expr = config["search_path"]["windows"]["expression"][1]

    assert re.compile(version_folder_expr).match(
        "Toon Boom Harmony 25.2 Premium"
    )
