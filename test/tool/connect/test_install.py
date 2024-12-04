import pytest
from click.testing import CliRunner
from tool.connect.commands.install import install


def test_install_pypi_package():
    runner = CliRunner()
    result = runner.invoke(install, ["example-package"])
    assert result.exit_code == 0
    assert "Package 'example-package' installed successfully." in result.output


def test_install_whl_file():
    runner = CliRunner()
    result = runner.invoke(install, ["example-package.whl"])
    assert result.exit_code == 0
    assert "Package 'example-package.whl' installed successfully." in result.output


def test_install_editable():
    runner = CliRunner()
    result = runner.invoke(install, ["-e", "example-package"])
    assert result.exit_code == 0
    assert "Package 'example-package' installed successfully." in result.output
