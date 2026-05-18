import re

import pytest
from packaging.version import Version

from ftrack_utils.version import (
    DEFAULT_VERSION_EXPRESSION,
    parse_application_version,
    resolve_marketing_version,
)


def test_parse_application_version_supports_standard_versions():
    assert str(parse_application_version("2024")) == "2024"
    assert str(parse_application_version("2024.1")) == "2024.1"
    assert str(parse_application_version("14.0b2")) == "14.0b2"


def test_parse_application_version_handles_v_delimited_dcc_patterns():
    assert str(parse_application_version("13.2v1")) == "13.2.1"
    assert str(parse_application_version("1.8v2b1")) == "1.8.2b1"


def test_parse_application_version_falls_back_to_zero_on_invalid_input():
    assert str(parse_application_version("not-a-version")) == "0"


def test_default_version_expression_extracts_dcc_style_version_token():
    path = "/path/to/x86/some/application/folder/v1.8v2b1/app.exe"
    match = DEFAULT_VERSION_EXPRESSION.search(path)
    assert match is not None
    assert match.group("version") == "1.8v2b1"


@pytest.mark.parametrize(
    "version, offset, path, expected_version, expected_suffix",
    [
        pytest.param(
            "27.7.0",
            1999,
            "/path/to/App (Beta)/App (Beta).app",
            "2026",
            " (beta)",
            id="beta-with-offset",
        ),
        pytest.param(
            "26.3.0",
            2000,
            "/path/to/App 2026/App.exe",
            "2026",
            "",
            id="stable-with-offset",
        ),
        pytest.param(
            "27.7.0",
            None,
            "/path/to/App (Beta)/App (Beta).app",
            "27.7.0",
            " (beta)",
            id="beta-without-offset",
        ),
        pytest.param(
            "2026",
            None,
            "/path/to/App 2026/App.app",
            "2026",
            "",
            id="stable-without-offset",
        ),
        pytest.param(
            "0",
            1999,
            "/path/to/App (Beta)/App.exe",
            "0",
            " (beta)",
            id="beta-zero-version-skips-offset",
        ),
    ],
)
def test_resolve_marketing_version(
    version, offset, path, expected_version, expected_suffix
):
    resolved, suffix = resolve_marketing_version(
        Version(version), offset, path
    )
    assert str(resolved) == expected_version
    assert suffix == expected_suffix


def test_project_version_expression_patterns_from_launch_configs_are_valid():
    patterns = [
        r"Nuke(?P<version>.*)\/.+$",
        r"(?P<version>[\d.]+[vabc]+[\dvabc.]*)",
        r"maya(?P<version>\d{4})",
    ]
    for pattern in patterns:
        re.compile(pattern)
