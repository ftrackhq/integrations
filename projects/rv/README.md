# RV Integration

ftrack RV integration enables seamless review workflows within Autodesk RV, allowing users to view and collaborate on media directly from ftrack.

## Overview

The ftrack RV integration provides two deployment options:

1. **Standalone Mode**: Install the RV package (`rvpkg`) directly in RV for use without ftrack Connect
2. **Connect Mode**: Install the Connect plugin to launch RV with review panels from ftrack Connect

Both modes integrate ftrack's review capabilities into RV, enabling users to browse assets, load media, and manage reviews within the RV interface.

---

## User Documentation

### Installation

#### Option 1: Standalone Mode (rvpkg only)

Use this method when you want to use RV with ftrack integration without installing ftrack Connect.

**Steps:**

1. **Download the integration package**
   - Obtain the latest RV Connect plugin package from your ftrack administrator or from the [ftrack Integrations releases](https://github.com/ftrackhq/integrations/releases)
   - The package is a `.zip` file containing both the Connect plugin and the RV package (`.rvpkg`)

2. **Extract the RV package**
   - Unzip the downloaded package
   - Locate the `ftrack-<version>.rvpkg` file inside the extracted folder

3. **Install the package in RV**
   - Launch RV
   - Navigate to **RV → Preferences** (or **Edit → Preferences** on Windows/Linux)
   - Go to the **Packages** tab
   - Click **Add Package** and select the `ftrack-<version>.rvpkg` file from the extracted folder
   - Restart RV

3. **Configure ftrack credentials**
   - Set the following environment variables before launching RV:
     - `FTRACK_SERVER`: Your ftrack server URL (e.g., `https://yourcompany.ftrackapp.com`)
     - `FTRACK_API_USER`: Your ftrack username or API user
     - `FTRACK_API_KEY`: Your ftrack API key

   **Windows (Command Prompt):**
   ```cmd
   set FTRACK_SERVER=https://yourcompany.ftrackapp.com
   set FTRACK_API_USER=your_username
   set FTRACK_API_KEY=your_api_key
   "C:\Program Files\Autodesk\RV-2024.1.0\bin\rv.exe"
   ```

   **macOS/Linux (Terminal):**
   ```bash
   export FTRACK_SERVER=https://yourcompany.ftrackapp.com
   export FTRACK_API_USER=your_username
   export FTRACK_API_KEY=your_api_key
   /Applications/RV.app/Contents/MacOS/RV
   ```

#### Option 2: Connect Mode (with ftrack Connect)

Use this method to launch RV directly from ftrack Connect with automatic session management and review panels.

**Steps:**

1. **Install ftrack Connect**
   - Download and install [ftrack Connect](https://www.ftrack.com/en/portfolio/connect) for your platform

2. **Install the RV integration plugin**

   **Method A: Using Connect Plugin Manager (Recommended)**
   
   - Launch ftrack Connect and log in
   - Open the **Plugin Manager** widget in Connect
   - Search for "RV" in the available plugins
   - Click **Install** on the RV integration plugin
   - The plugin will be downloaded and installed automatically
   - Restart ftrack Connect
   
   **Method B: Manual Installation from GitHub**
   
   If the plugin is not available in the Plugin Manager, or you need a specific version:
   
   - Download the latest RV Connect plugin package from the [ftrack Integrations releases](https://github.com/ftrackhq/integrations/releases)
   - The package is a `.zip` file containing both the Connect plugin and the bundled RV package (`.rvpkg`)
   - Extract the downloaded `.zip` file to a location on your system
   - Launch ftrack Connect
   - Go to the plugins configuration (via Connect's plugin settings or the plugins directory)
   - Add the extracted plugin folder to your Connect plugins directory
   - The RV package (`.rvpkg`) is already bundled within the Connect plugin and will be deployed automatically
   - Restart ftrack Connect

3. **Linux-specific requirement**
   - On Linux systems, set the `RV_INSTALLATION_PATH` environment variable to point to your RV installation root directory:
   
   ```bash
   export RV_INSTALLATION_PATH=/usr/local/rv
   ```

   - Add this to your shell profile (`~/.bashrc` or `~/.zshrc`) to make it persistent

### Usage

#### Launching RV

**With ftrack Connect:**
1. Launch ftrack Connect and log in
2. Navigate to a Project, Task, or Asset Version in the Connect interface
3. Click the **RV** action button to launch RV with the review panel pre-loaded
4. The ftrack mode will be automatically activated with `-flags ModeManagerPreload=ftrack`

**Standalone (without Connect):**
1. Launch RV with the environment variables configured (see Installation above)
2. The ftrack integration will be available in the RV interface
3. Access ftrack features through the RV menu or keyboard shortcuts (see below)

#### Key Features

- **Asset Loading**: Browse and load media from ftrack directly within RV
- **Review Integration**: View and manage review sessions
- **Version Comparison**: Compare multiple versions side-by-side
- **Annotation Support**: View annotations and notes from ftrack reviews
- **Session Management**: Automatically authenticated sessions when launched from Connect

#### Keyboard Shortcuts

The ftrack mode provides keyboard bindings for quick access to integration features. Refer to the RV interface or contact your administrator for the specific keyboard shortcuts configured for your installation.

### Platform-Specific Notes

#### Windows
- RV is typically installed in `C:\Program Files\Autodesk\RV-<version>\bin\rv.exe`
- The integration supports all Autodesk/Shotgun/ShotGrid RV variants

#### macOS
- RV is typically installed in `/Applications/RV.app`
- Launch using the full path: `/Applications/RV.app/Contents/MacOS/RV`

#### Linux
- RV installation path must be specified via `RV_INSTALLATION_PATH` when using Connect mode
- Default path if not specified: `/usr/local/rv`
- Supports both CentOS 7 and Rocky Linux 9 RV distributions

### Troubleshooting

**Problem: ftrack mode not loading**
- Verify the `.rvpkg` file is properly installed in RV Preferences → Packages
- Check that environment variables are set correctly
- Review RV console output for error messages

**Problem: Cannot connect to ftrack**
- Verify `FTRACK_SERVER`, `FTRACK_API_USER`, and `FTRACK_API_KEY` are correctly set
- Test API credentials using the [ftrack Python API](https://github.com/ftrackhq/ftrack-python-api) independently
- Check network connectivity and firewall settings

**Problem: RV not launching from Connect (Linux)**
- Ensure `RV_INSTALLATION_PATH` is set and points to the correct directory
- Verify RV binary is executable: `chmod +x $RV_INSTALLATION_PATH/bin/rv`

**Problem: Dependencies missing**
- The integration bundles all required dependencies
- If you see import errors, verify the `.rvpkg` file is complete and not corrupted

### Getting Help

For additional support:
- Check the [ftrack Help Center](https://help.ftrack.com)
- Contact your ftrack administrator
- Report issues at [GitHub Issues](https://github.com/ftrackhq/integrations/issues)

---

## Developer Documentation

This section is for developers who want to build, modify, or contribute to the RV integration.

### Prerequisites

- **Python**: Version 3.13 (specified in `pyproject.toml`)
- **uv**: Modern Python package manager - [Install uv](https://docs.astral.sh/uv/)
- **RV**: Autodesk RV installation for testing
- **Git**: Version control

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ftrackhq/integrations.git
   cd integrations/projects/rv
   ```

2. **Create and activate a virtual environment**
   
   **Linux/macOS:**
   ```bash
   uv venv .venv
   source .venv/bin/activate
   ```
   
   **Windows (PowerShell):**
   ```powershell
   uv venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```bash
   uv pip install -e ".[dev]"
   ```

### Project Structure

```
projects/rv/
├── source/ftrack_rv/          # Python package source
├── resource/plugin/           # RV plugin source (PACKAGE.yml, Python modules)
│   ├── PACKAGE.yml           # RV package manifest
│   ├── ftrack.py             # Main RV mode implementation
│   ├── ftrack_rv_api.py      # ftrack API integration
│   └── ftrack_logging.py     # Logging configuration
├── connect-plugin/            # ftrack Connect plugin hooks
│   └── hook/
│       ├── discover_ftrack_rv.py
│       └── ftrack_rv_launcher.py
├── pyproject.toml            # Project metadata and dependencies
├── release_notes.md          # Release changelog
└── README.md                 # This file
```

### Building the Plugin

The build process creates two artifacts:

1. **RV Package (`.rvpkg`)**: Standalone RV plugin
2. **Connect Plugin (`.zip`)**: Connect plugin with bundled `.rvpkg`

#### Step 1: Prepare for Release

1. **Update release notes**
   ```bash
   # Edit release_notes.md with changes for this version
   ```

2. **Set version number**
   - Update version in `pyproject.toml` (use semantic versioning: `MAJOR.MINOR.PATCH`)
   - For prereleases use: `MAJOR.MINOR.PATCHrcN` (e.g., `26.3.0rc1`)
   
   ```toml
   # pyproject.toml
   [project]
   version = "26.3.0"
   ```

3. **Bump Connect plugin version**
   ```bash
   # Edit connect-plugin/__version__.py
   echo '__version__ = "26.3.0"' > connect-plugin/__version__.py
   ```

4. **Commit and tag**
   ```bash
   git add .
   git commit -m "Release v26.3.0"
   git tag v26.3.0
   git push origin main --tags
   ```

#### Step 2: Build the RV Package (.rvpkg)

The `.rvpkg` file is a zip archive containing the RV plugin code and bundled dependencies.

```bash
cd projects/rv
uv run python ../../tools/build.py --output_path . build_rvpkg .
```

**What this does:**
- Reads version from `pyproject.toml`
- Installs Python dependencies into a temporary folder
- Creates `dependencies.zip` containing all required packages (ftrack-python-api, etc.)
- Copies files from `resource/plugin/` to staging area
- Renames `PACKAGE.yml` to `PACKAGE` (RV requirement)
- Replaces `{VERSION}` placeholders in the PACKAGE file
- Creates `ftrack-<MAJOR.MINOR>.rvpkg` (e.g., `ftrack-26.3.rvpkg`)

**Output:** `./ftrack-26.3.rvpkg`

#### Step 3: Build the Python Package (Required for Connect Plugin)

The Connect plugin requires a Python wheel to install the `ftrack_rv` package.

```bash
cd projects/rv
uv build
```

**What this does:**
- Reads project metadata from `pyproject.toml`
- Builds a Python wheel (`.whl`) and source distribution (`.tar.gz`)
- Places artifacts in `dist/` folder

**Output:** `dist/ftrack_rv-26.3.0-py3-none-any.whl`

#### Step 4: Build the Connect Plugin

The Connect plugin bundles the `.rvpkg` file along with launcher hooks.

```bash
cd projects/rv
uv run python ../../tools/build.py --include_assets ./ftrack-26.3.rvpkg build_connect_plugin .
```

**What this does:**
- Locates the Python wheel built in Step 3
- Creates a staging directory with Connect plugin structure
- Copies files from `connect-plugin/hook/` to staging
- Installs the wheel and Connect dependencies into staging
- Copies the `.rvpkg` file specified in `--include_assets` into the staging directory
- Creates a `.zip` archive in the `dist/` folder

**Output:** `dist/ftrack-rv-26.3.0.zip`

**Contents of the zip:**
```
ftrack-rv-26.3.0/
├── hook/
│   ├── discover_ftrack_rv.py
│   └── ftrack_rv_launcher.py
├── dependencies/              # Connect dependencies
│   ├── ftrack_rv/            # From the wheel
│   ├── ftrack_python_api/
│   ├── ftrack_utils/
│   └── ...
├── ftrack-26.3.rvpkg         # Bundled RV package
└── __version__.py
```

#### Step 5: Build with Test PyPI (Optional)

If using beta/experimental dependencies from Test PyPI:

```bash
cd projects/rv
uv run python ../../tools/build.py --testpypi --include_assets ./ftrack-26.3.rvpkg build_connect_plugin .
```

### Build Script Options

The `build.py` script supports several options:

| Option | Description |
|--------|-------------|
| `--output_path <path>` | Output directory for build artifacts |
| `--include_assets <files>` | Comma-separated list of files to bundle (e.g., `.rvpkg`) |
| `--testpypi` | Use Test PyPI for experimental dependencies |
| `--platform_dependent` | Add platform suffix to output filename |
| `--remove_intermediate_folder` | Clean up staging directories after build |

### Testing the Build Locally

#### Test the RV Package

1. **Install in RV:**
   ```bash
   # Launch RV and go to Preferences → Packages
   # Or copy to RV's package directory:
   cp ./ftrack-26.3.rvpkg ~/Library/Application\ Support/RV/Packages/  # macOS
   ```

2. **Launch RV with ftrack mode:**
   ```bash
   export FTRACK_SERVER=https://yourcompany.ftrackapp.com
   export FTRACK_API_USER=your_username
   export FTRACK_API_KEY=your_api_key
   /Applications/RV.app/Contents/MacOS/RV -flags ModeManagerPreload=ftrack
   ```

3. **Verify:**
   - Check RV console for ftrack plugin initialization logs
   - Verify ftrack mode is active in RV

#### Test the Connect Plugin

1. **Install in Connect:**
   ```bash
   # Extract the zip
   unzip dist/ftrack-rv-26.3.0.zip -d ~/ftrack-connect-plugins/
   
   # Or use Connect's plugin manager:
   # Connect → Settings → Plugins → Add Plugin → select extracted folder
   ```

2. **Launch RV from Connect:**
   - Open ftrack Connect
   - Navigate to a Task or Asset Version
   - Click the RV action button
   - Verify RV launches with ftrack integration active

### CI/CD Build

For automated builds, see the monorepo CI/CD configuration:

```bash
# The CI workflow typically runs:
# 1. Build rvpkg
# 2. Build Connect plugin with bundled rvpkg
# 3. Run tests
# 4. Upload artifacts to releases
```

Refer to `.github/workflows/` in the monorepo root for CI configuration.

### Troubleshooting Development Issues

**Problem: Build fails with dependency errors**
- Ensure virtual environment is activated
- Try: `uv pip install -e ".[dev]"` to reinstall dependencies
- Check `pyproject.toml` for correct dependency versions

**Problem: uv not found**
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Unix) or `irm https://astral.sh/uv/install.ps1 | iex` (Windows)

**Problem: Wrong Python version**
- The project requires Python 3.13
- Use `uv python install 3.13` to install the correct version

**Problem: RV package doesn't load**
- Check RV console output for errors
- Verify `dependencies.zip` is present in the `.rvpkg` file
- Ensure `PACKAGE` file (not `PACKAGE.yml`) exists in the package

### Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Test thoroughly with both standalone and Connect modes
4. Update release notes
5. Submit a pull request

### Additional Resources

- [ftrack Python API Documentation](https://ftrack-python-api.readthedocs.io/)
- [RV Documentation](https://help.autodesk.com/view/SGSUB/ENU/)
- [ftrack Connect Plugin Development](https://help.ftrack.com/en/articles/1040469-developing-connect-plugins)
- [uv Documentation](https://docs.astral.sh/uv/)
