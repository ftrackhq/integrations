# Ftrack Connect Installation

## Installation methods
We provide three ways to install ftrack connect on your machine. Choose the appropriate method based on your requirements/usecase.

### Standalone Installation Scripts

These scripts can be copied and pasted into your terminal.

> [!IMPORTANT] Know what you execute
> While we put a lot of effort into making these scripts safe to execute on any system, run them at your own risk. When executing scripts/code from a third party, always check the code first.

> [!WARNING] UV Installation
> During the installation process, we'll make use of the `uv` installation script.
> 
#### Linux / macos
```shell
curl https://install.sh | sh
```
This command downloads the installation script via `curl` and executes it in a unix shell `sh`.

- `curl` Command to download anything from a url.
- `| sh` Pass/Pipe the contenst of `install.sh` to `shell` and execute them.

#### Windows
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://install.ps1 | iex"
```
We're using powershell to download and execute the installation script.

- `powershell` Execute the following commands in powershell.
- `-ExecutionPolicy Bypass` will attempt 
- `-c` Execute everything after this
- `irm` Shorthand for `Invoke-RestMethod`. Equivalent to `curl`. Will downl7aod the script.
- `| iex` Pass/Pipe the contents of the `install.ps1` script to `iex` and execute them.

### Installation as a python package
When you already have a working python interpreter/environment, you can install ftrack connect via `pip` or any alternative python package manager.

### Standalone UI Installer
...