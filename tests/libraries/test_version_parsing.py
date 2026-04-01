import re

from ftrack_utils.version import (
    DEFAULT_VERSION_EXPRESSION,
    parse_application_version,
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


def test_project_version_expression_patterns_from_launch_configs_are_valid():
    patterns = [
        r"Nuke(?P<version>.*)\/.+$",
        r"(?P<version>[\d.]+[vabc]+[\dvabc.]*)",
        r"maya(?P<version>\d{4})",
    ]
    for pattern in patterns:
        re.compile(pattern)
