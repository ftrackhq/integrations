# framework-maya-deadline

Deadline Cloud extension for the ftrack Maya integration.

Loads alongside `framework-maya` as a separate Connect plugin, adding scene dependency tracing and sync to AWS Deadline Cloud / S3 directly from within Maya.

## How it works

When both `framework-maya` and `framework-maya-deadline` are installed in Connect, launching Maya activates both plugins. This extension bootstraps independently via its own `userSetup.py` on `MAYA_SCRIPT_PATH` and adds a "Deadline Cloud" submenu to the existing ftrack menu.

### Menu items

- **Publish to Deadline...** — opens the publish dialog (non-blocking)
- **Scene Status...** — opens the scene status dialog (non-blocking)
- **Sync on Save** — toggle: when enabled, shows publish dialog after every scene save
- **Sync on Open** — toggle: when enabled, shows a modal status dialog *before* a scene opens (via `MSceneMessage.kBeforeOpenCheck`), allowing asset sync to complete before Maya resolves references

Toggle state is persisted across sessions via Maya `optionVar`.

## Building

```bash
# Build the wheel
cd projects/framework-maya-deadline
uv build

# Build the Connect plugin archive
cd ../..
uv run python tools/build.py \
    --include_resources resource/bootstrap \
    build_connect_plugin \
    projects/framework-maya-deadline
```

Output: `dist/ftrack-framework-maya-deadline-X.Y.Z.zip`

Deploy the unzipped directory to `FTRACK_CONNECT_PLUGIN_PATH`.

## Testing

Requires `dcc-test-harness` and a built `framework-maya` plugin:

```bash
cd /path/to/dcc-test-harness
uv run python -m pytest /path/to/framework-maya-deadline/tests/ -v \
    --dcc-connect-plugin /path/to/framework-maya/dist/ftrack-framework-maya-X.Y.Z \
    --dcc-connect-plugin /path/to/framework-maya-deadline
```

The first `--dcc-connect-plugin` is the primary (provides Maya discovery). The second layers the extension on top.

## Architecture

- **Connect hook** (`connect-plugin/hook/discover_ftrack_maya_deadline.py`): subscribes to `maya*` launch events at priority 50 (after framework-maya's 40). Directly modifies the subprocess environment dict (`event["data"]["options"]["env"]`) to inject `PYTHONPATH` and `MAYA_SCRIPT_PATH`, bypassing Connect's integrations mechanism.
- **Bootstrap** (`resource/bootstrap/userSetup.py`): deferred import of `ftrack_framework_maya_deadline`
- **Package** (`source/ftrack_framework_maya_deadline/`):
  - `__init__.py` — creates "Deadline Cloud" submenu, registers menu items, restores callback state from prefs
  - `callbacks.py` — SceneSaved scriptJob (post-save) + kBeforeOpenCheck callback (pre-open modal), opt-in toggles via optionVar, dialog singleton management
  - `utils.py` — PySide6/shiboken6 fallback, Maya main window helper
  - `dialogs/save_dialog.py` — publish dialog shell (non-blocking)
  - `dialogs/open_dialog.py` — scene status dialog shell (modal when triggered by kBeforeOpenCheck, with Continue/Cancel buttons)
- **DCC config** (`extensions/deadline.yaml`): stub for the build system
