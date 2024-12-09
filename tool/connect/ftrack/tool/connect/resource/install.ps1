
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

$global:stdout = [Console]::Out
$global:stderr = [Console]::Error

function Set-DisableOutput() {
    $log_path = New-TemporaryFile
    # Redirect stdout to a file
    [Console]::Out.SetOutputStream([IO.StreamWriter]::new($log_path))
    # Redirect stderr to a file
    [Console]::Error.SetOutputStream([IO.StreamWriter]::new($log_path))
}

function Set-EnableOutput() {
    # Restore original output streams
    [Console]::Out.SetOutputStream($global:stdout)
    [Console]::Error.SetOutputStream($global:stderr)
}

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
    $temp_path = Join-Path "${parent}" "ftrack.${uid}"
    New-Item -ItemType Directory $temp_path
}

function New-InstallDirectory() {
    $install_path = Join-Path "${env:LOCALAPPDATA}" "ftrack" "connect4"
    New-Item -ItemType Directory $install_path -Force
}

function Invoke-UVInstaller() {
    Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 | Invoke-Expression
}

function New-UVVirtualEnv($temp_directory, $install_directory) {
    $install_venv_path = Join-Path $install_directory ".venv"
    $temp_uv_executable_path = Join-Path "${temp_directory}" "uv" "bin" "uv"

    Start-Process $temp_uv_executable_path -ArgumentList "venv ${install_venv_path} --python 3.11" -NoNewWindow -Wait
    Start-Process $temp_uv_executable_path -ArgumentList "pip install uv" -WorkingDirectory $install_directory -NoNewWindow -Wait
}

function Invoke-InstallPackageIntoVenv($install_directory, $package_name) {
    $uv_executable_path = Join-Path $install_directory ".venv" "Scripts" "uv"
    Start-Process $uv_executable_path -ArgumentList "pip install ${package_name}" -WorkingDirectory $install_directory -NoNewWindow -Wait
}

function Invoke-ConnectInstaller() {
    $temp_directory = New-TemporaryDirectory
    $install_directory = New-InstallDirectory

    Set-EnvironmentVariables $temp_directory $install_directory

    Invoke-UVInstaller

    New-UVVirtualEnv $temp_directory $install_directory

    # these packages are just examples for testing purposes
    Invoke-InstallPackageIntoVenv $install_directory "poetry"
    Invoke-InstallPackageIntoVenv $install_directory "ftrack-utils"
}

try {
    Invoke-ConnectInstaller

    Write-Host "Environment Variables for UV installation have been set:" -ForegroundColor DarkCyan
    Write-Host "--------------------------------------------------------" -ForegroundColor DarkCyan
    @(
        [PSCustomObject]@{
            UV_INSTALL_DIR=$env:UV_INSTALL_DIR;
            UV_CACHE_DIR=$env:UV_CACHE_DIR;
            UV_PYTHON_INSTALL_DIR=$env:UV_PYTHON_INSTALL_DIR;
            UV_NO_MODIFY_PATH=$env:UV_NO_MODIFY_PATH;
            UV_UNMANAGED_INSTALL=$env:UV_UNMANAGED_INSTALL;
            INSTALLER_NO_MODIFY_PATH=$env:INSTALLER_NO_MODIFY_PATH
        }
    ) | Format-List
}  catch {
    # Log the error
    # point to the installation log.
}