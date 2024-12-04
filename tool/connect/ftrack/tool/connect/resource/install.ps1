
<#
.SYNOPSIS
The installer for ftrack connect.

.DESCRIPTION
This script will install ftrack connect.

.PARAMETER Help
Display help.
#>

param (
    [Parameter(HelpMessage = "Print Help")]
    [switch]$Help
)

function Set-EnvironmentVariables($temp_directory, $install_directory) {
    $env:UV_NO_MODIFY_PATH = 1
    $env:INSTALLER_NO_MODIFY_PATH = 1
    $env:UV_UNMANAGED_INSTALL = 1
    $env:UV_INSTALL_DIR = Join-Path $temp_directory "uv" "bin"
    $env:UV_CACHE_DIR = Join-Path $temp_directory "uv" "cache"
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $temp_directory "uv" "python"
}

function New-TemporaryDirectory() {
    $parent = [System.IO.Path]::GetTempPath()
    $uid = [System.Guid]::NewGuid()
    $temp_path = Join-Path $parent "ftrack.${uid}"
    New-Item -ItemType Directory $temp_path
}

function New-InstallDirectory() {
    $install_path = Join-Path "${env:LOCALAPPDATA}" "ftrack" "connect4"
    New-Item -ItemType Directory $install_path -Force
}

function Invoke-UVInstaller($temp_directory) {
    Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 | Invoke-Expression
}

$temp_directory = New-TemporaryDirectory
$install_directory = New-InstallDirectory

Set-EnvironmentVariables $temp_directory $install_directory

Invoke-UVInstaller $temp_directory

$uv_executable = Join-Path $temp_directory "uv" "bin" "uv"
$venv_path = Join-Path $install_directory ".venv"


Start-Process $uv_executable -ArgumentList "venv ${venv_path} --python 3.10.15" -NoNewWindow

