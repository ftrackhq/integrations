import pytest
from click.testing import CliRunner
from tool.connect.commands.uv import uv


def test_uv_command():
    runner = CliRunner()
    result = runner.invoke(uv, ["--version"])
    assert result.exit_code == 0
    assert "uv" in result.output
