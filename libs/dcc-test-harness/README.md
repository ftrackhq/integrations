# dcc-test-harness

A pytest-based test framework for DCC (Digital Content Creation) applications. Write tests in standard Python and pytest while they execute inside Maya, Nuke, Houdini, or any Qt-based DCC.

> Vendored into the integrations monorepo from
> [ftrackhq/dcc-test-harness](https://github.com/ftrackhq/dcc-test-harness)
> @ `dev` (a273c58) so all integration projects can consume it as a
> local path dependency.

## How it works

```
pytest (Python 3.13)              Maya / Nuke / Houdini
---------------------             ----------------------
                                  Embedded Python interpreter
  DCCClient  ── JSON-RPC/TCP ──>  TestServer (QTimer dispatch)
  WidgetProxy                     CommandDispatcher
  DCCUI                           WidgetRegistry
```

The harness runs **outside** the DCC as a normal pytest session. It communicates with a small TCP server running **inside** the DCC's Python interpreter. Commands are dispatched on the DCC's main thread via a QTimer, so all Qt and DCC API calls are thread-safe.

The harness is DCC-agnostic. It provides the protocol, client, fixtures, and Qt helpers. When an ftrack integration is available, the harness launches the DCC automatically using its connect launch config. For custom setups, you can provide your own launcher class.

## Installation

Add as a test dependency in your integration project (inside this
monorepo), pointing at the library via a path source:

```toml
# projects/framework-<dcc>/pyproject.toml
[project.optional-dependencies]
test = [
    "dcc-test-harness[test]",
]

[tool.uv.sources]
dcc-test-harness = { path = "../../libs/dcc-test-harness" }
ftrack-connect = { path = "../../apps/connect" }

[tool.uv]
override-dependencies = [
    "ftrack-connect @ file:///${PROJECT_ROOT}/../../apps/connect",
]
```

The `ftrack-connect` source and override are required because uv does
not apply a path dependency's own `tool.uv.sources` transitively —
without them the harness's `ftrack-connect` dependency would resolve
from PyPI.

Then install from the project directory:

```bash
uv sync --extra test
```

## Quick start

If you have an ftrack integration project (e.g. `framework-maya`), the harness can launch the DCC and configure the ftrack environment automatically. No custom launcher code needed.

### Step 1: Create a conftest with a scene-reset fixture

```python
# tests/conftest.py
import pytest
from dcc_test_harness.client import DCCClient

@pytest.fixture
def maya(dcc_client: DCCClient):
    """Per-test fixture that resets the Maya scene."""
    dcc_client.execute(
        "import maya.cmds; maya.cmds.file(new=True, f=True)"
    )
    yield dcc_client
```

### Step 2: Write tests

```python
# tests/test_smoke.py

class TestConnection:
    def test_ping(self, dcc_client):
        """Verify the RPC connection is alive."""
        assert dcc_client.ping()


class TestMayaCmds:
    def test_create_and_query(self, maya):
        """Create a node and verify it exists."""
        maya.execute("""
import maya.cmds as mc
mc.polyCube(name='testCube')
""")
        result = maya.execute("""
import maya.cmds as mc
__result__ = mc.objExists('testCube')
""")
        assert result is True
```

### Step 3: Run the tests

Point `--dcc-connect-plugin` at a built connect plugin directory:

```bash
uv run python -m pytest tests/ -v \
    --dcc-connect-plugin path/to/dist/ftrack-framework-maya-X.Y.Z
```

The harness reads the YAML launch config from the plugin, auto-detects that it's a Maya plugin, discovers Maya on your system, configures the ftrack environment (PYTHONPATH, dependencies, bootstrap, extensions, credentials), injects the test server, and launches. The built plugin includes all ftrack packages in its `dependencies/` directory, so the full integration is available inside Maya.

### Testing with multiple plugins

Pass `--dcc-connect-plugin` multiple times to layer extension plugins on top of a primary plugin:

```bash
uv run python -m pytest tests/ -v \
    --dcc-connect-plugin path/to/dist/ftrack-framework-maya-X.Y.Z \
    --dcc-connect-plugin path/to/framework-maya-deadline
```

The first plugin is the primary (provides DCC discovery and launch config). Additional plugins have their `dependencies/`, `source/`, and `bootstrap/` directories added to PYTHONPATH and the DCC script path. Source project directories are supported -- the harness detects the layout and adds `source/` to PYTHONPATH so the package is importable without building.

### Prerequisites

The ftrack integration requires credentials to connect to the server. The harness finds them automatically from **Connect's stored credentials** (`~/Library/Application Support/ftrack-connect/credentials.json` on macOS). Just log in via ftrack Connect once and the credentials persist.

Alternatively, set `FTRACK_SERVER` and `FTRACK_API_KEY` environment variables.

### What the ConnectLauncher sets up

The harness reads the connect plugin directory and configures:

| Environment | Source |
|---|---|
| `PYTHONPATH` | `dependencies/` + `resource/bootstrap/` + harness package |
| `MAYA_SCRIPT_PATH` | `resource/bootstrap/` (loads `userSetup.py` on Maya startup) |
| `FTRACK_MAYA_VERSION` | Extracted from the discovered Maya path |
| `FTRACK_FRAMEWORK_EXTENSIONS_PATH` | Resolved from the YAML `extensions_path` entries |
| `FTRACK_SERVER` / `FTRACK_API_KEY` | From env vars or Connect's stored credentials |
| `FTRACK_EVENT_SERVER` | Set to `FTRACK_SERVER` (for the WebSocket event hub) |
| `SSL_CERT_FILE` | System default CA bundle (DCCs bundle outdated certs) |

This replicates the environment that ftrack-connect would create when launching a DCC. The full integration loads inside Maya: ftrack menu, Publisher/Opener dialogs, server connection, and event hub.

### Harness fixtures

The harness auto-registers these fixtures via a pytest plugin:

| Fixture | Scope | Description |
|---|---|---|
| `dcc_launcher` | session | Creates a `ConnectLauncher` from `--dcc-connect-plugin`. Override in your `conftest.py` for custom launch behavior. |
| `dcc_process` | session | Launches the DCC via `dcc_launcher`. Yields a `DCCProcess`. Shuts down the DCC after all tests. |
| `dcc_client` | session | A connected `DCCClient` ready to send commands. Depends on `dcc_process`. |
| `dcc_ui` | session | A `DCCUI` helper for Qt widget interaction. Depends on `dcc_client`. |

## Executing code inside the DCC

The `dcc_client` (or your wrapper fixture like `maya`) gives you two ways to run code inside the DCC:

### `execute(code)` -- run a block of Python

Runs arbitrary Python inside the DCC. Set `__result__` to return a value:

```python
def test_execution(maya):
    result = maya.execute("""
import maya.cmds as mc
mc.polyCube(name='cube1')
__result__ = mc.ls('cube1', type='transform')
""")
    assert result == ["cube1"]
```

The return value must be JSON-serializable (strings, numbers, bools, lists, dicts, None). Non-serializable objects are converted to strings.

### `evaluate(expression)` -- evaluate a single expression

```python
def test_eval(maya):
    assert maya.evaluate("1 + 1") == 2
    assert maya.evaluate("'hello ' + 'world'") == "hello world"
```

## Testing Qt widgets

The harness can inspect, interact with, and assert on any Qt widget in the DCC's UI.

### Finding widgets

```python
def test_find_main_window(dcc_client):
    widget = dcc_client.find_widget(
        widget_type="QMainWindow",
        visible_only=False,
    )
    assert widget is not None

def test_find_all_buttons(dcc_client):
    buttons = dcc_client.find_widgets(
        widget_type="QPushButton",
    )
    assert len(buttons) > 0
```

Query parameters for `find_widget` and `find_widgets`:

| Parameter | Type | Description |
|---|---|---|
| `widget_type` | `str` | Qt class name, e.g. `"QPushButton"`, `"QDialog"` |
| `object_name` | `str` | The widget's `objectName()` |
| `text` | `str` | The widget's displayed text |
| `window_title` | `str` | Filter to widgets under a specific top-level window |
| `visible_only` | `bool` | Only match visible widgets (default: `True`) |

### Waiting for widgets

Use `wait_for_widget` when a widget appears asynchronously (e.g. after triggering a menu action):

```python
def test_wait_for_dialog(dcc_client):
    # Trigger something that opens a dialog...
    dcc_client.execute("open_my_dialog()")

    widget = dcc_client.wait_for_widget(
        widget_type="QDialog",
        text="My Dialog Title",
        timeout=5.0,
    )
    assert widget is not None
```

Raises `WidgetNotFoundError` if the widget doesn't appear within the timeout.

### Interacting with widgets

`find_widget` and `find_widgets` return `WidgetProxy` objects. Use them to click, type, and inspect:

```python
def test_button_click(dcc_client):
    button = dcc_client.find_widget(
        widget_type="QPushButton",
        text="Apply",
    )
    button.click()
```

Available `WidgetProxy` methods:

| Method | Description |
|---|---|
| `click()` | Click the widget (buttons, actions, or synthetic mouse event) |
| `double_click()` | Double-click the widget |
| `set_text(text)` | Set text on QLineEdit or QTextEdit |
| `set_value(value)` | Set value on QSpinBox, QDoubleSpinBox, QSlider |
| `set_combo_text(text)` | Select a QComboBox item by display text |
| `set_combo_index(index)` | Select a QComboBox item by index |
| `set_checked(checked)` | Check or uncheck a QCheckBox or QRadioButton |
| `close()` | Close the widget |
| `children(**query)` | Find child widgets matching a query |
| `parent()` | Get the parent widget |
| `refresh()` | Re-fetch the widget's current state from the DCC |

Available `WidgetProxy` properties:

| Property | Description |
|---|---|
| `widget_id` | Internal ID for the widget |
| `widget_type` | Qt class name (e.g. `"QPushButton"`) |
| `object_name` | The widget's `objectName()` |
| `text` | Displayed text |
| `visible` | Whether the widget is visible |
| `enabled` | Whether the widget is enabled |

### High-level UI helpers (`dcc_ui`)

The `dcc_ui` fixture provides a higher-level API for common patterns:

```python
def test_dialog_workflow(dcc_ui):
    # Wait for a dialog to appear
    dialog = dcc_ui.wait_for_dialog(title="Publish")

    # Fill form fields by label text or objectName
    dcc_ui.fill_form(dialog, {
        "Comment": "automated test",
        "Version": 2,
    })

    # Close all open dialogs
    dcc_ui.close_all_dialogs()
```

Assertion helpers:

```python
def test_ui_state(dcc_ui):
    dcc_ui.assert_widget_exists(
        widget_type="QPushButton", text="Submit"
    )
    dcc_ui.assert_widget_not_exists(
        widget_type="QDialog", text="Error"
    )
    dcc_ui.assert_widget_text(
        "Ready", object_name="statusLabel"
    )
    dcc_ui.assert_widget_visible(object_name="toolbar")
    dcc_ui.assert_widget_enabled(object_name="submitButton")
```

## Testing DCC menus

DCC menus are often built lazily and don't live in the Qt widget tree until opened. Use `execute` with the DCC's native API to interact with them:

```python
def test_file_menu_has_new_scene(dcc_client):
    result = dcc_client.execute("""
import maya.cmds as mc
import maya.mel

menus = mc.window('MayaWindow', query=True, menuArray=True) or []
found = False
for m in menus:
    label = mc.menu(m, query=True, label=True)
    if label == 'File':
        # Force the menu to populate (Maya builds menus lazily)
        pmc = mc.menu(m, query=True, postMenuCommand=True)
        if pmc:
            maya.mel.eval(str(pmc))
        items = mc.menu(m, query=True, itemArray=True) or []
        for item in items:
            if mc.menuItem(item, query=True, label=True) == 'New Scene':
                found = True
                break
        break

__result__ = found
""")
    assert result is True
```

## Testing callbacks

Register callbacks, trigger them, and verify they fired:

```python
def test_save_callback(maya):
    # Register a callback
    maya.execute("""
import maya.api.OpenMaya as om2

__builtins__['_test_save_fired'] = False

def _on_before_save(client_data):
    __builtins__['_test_save_fired'] = True

__builtins__['_test_save_cb_id'] = om2.MSceneMessage.addCallback(
    om2.MSceneMessage.kBeforeSave, _on_before_save
)
""")

    # Trigger the callback
    maya.execute("""
import maya.cmds as mc
mc.file(rename='/tmp/test_callback.ma')
mc.file(save=True, type='mayaAscii')
""")

    # Verify it fired
    assert maya.evaluate("_test_save_fired") is True

    # Clean up
    maya.execute("""
import maya.api.OpenMaya as om2
om2.MMessage.removeCallback(__builtins__['_test_save_cb_id'])
del __builtins__['_test_save_fired']
del __builtins__['_test_save_cb_id']
""")
```

Store callback state on `__builtins__` so it persists across separate `execute` calls within the same test.

## pytest CLI options

Control DCC launching and connection from the command line:

| Option | Default | Description |
|---|---|---|
| `--dcc-connect-plugin` | | Path to ftrack connect plugin (built or source). Can be specified multiple times; first is primary, rest layered on top. |
| `--dcc-app` | auto-detect | Override DCC type (e.g. `maya`). Normally detected from the plugin's launch config. |
| `--dcc-version` | newest | DCC version to use (e.g. `2025`). Prefix-matched against discovered versions. |
| `--dcc-launch` | `true` | Auto-launch the DCC via the launcher |
| `--dcc-no-launch` | | Connect to an already-running DCC instance instead |
| `--dcc-executable` | auto-detect | Path to the DCC binary (overrides auto-discovery) |
| `--dcc-host` | `127.0.0.1` | RPC server host |
| `--dcc-port` | `0` (auto) | RPC server port (required with `--dcc-no-launch`) |
| `--dcc-timeout` | `10.0` | Timeout for individual RPC calls (seconds) |
| `--dcc-startup-timeout` | `60.0` | Timeout for DCC startup (seconds) |

### Connecting to a running DCC

If you already have a DCC open with the test server running, skip the auto-launch:

```bash
uv run python -m pytest tests/ --dcc-no-launch --dcc-port 9876
```

To start the server manually inside a DCC's script editor:

```python
from dcc_test_harness.server import start
start(port=9876)
```

## DCC shutdown

The harness shuts down the DCC cleanly via a `quit_fn` callback that runs on the main thread through the Qt event loop. This is important because sending SIGTERM to a DCC crashes Qt mid-paint on macOS.

The shutdown sequence is:

1. `dcc_client` fixture teardown sends a `shutdown` RPC
2. The server schedules the quit on the main thread via QTimer
3. `quit_fn` runs (e.g. `maya.cmds.quit(force=True)`)
4. The DCC exits cleanly

Always provide a `quit_fn` in your launcher's `_build_server_startup_code` call.

## Error handling

The harness provides specific exception types:

| Exception | When |
|---|---|
| `DCCConnectionError` | TCP connection fails or is lost |
| `RPCError` | Code execution fails inside the DCC (includes remote traceback) |
| `RPCTimeoutError` | An RPC call exceeds the timeout |
| `WidgetNotFoundError` | A widget query or `wait_for_widget` finds no match |

All inherit from `DCCTestHarnessError`.

When an `RPCError` is raised, the remote traceback from inside the DCC is available via `error.remote_traceback`:

```python
import pytest
from dcc_test_harness.exceptions import RPCError

def test_error_handling(maya):
    with pytest.raises(RPCError) as exc_info:
        maya.execute("raise ValueError('intentional')")
    assert "intentional" in str(exc_info.value)
```

## Project layout

```
src/dcc_test_harness/
    __init__.py            Package root
    _protocol.py           JSON-RPC 2.0 framing (length-prefixed TCP)
    _dcc_profiles.py       DCC profiles (quit_fn, CLI flags, env var names)
    _app_discovery.py      Filesystem search for DCC executables from YAML
    exceptions.py          Error hierarchy
    server.py              DCC-side: TCP server, QTimer dispatch, Qt widget ops
    client.py              External: DCCClient, WidgetProxy
    qt_helpers.py          External: DCCUI (dialogs, forms, assertions)
    launcher.py            Launcher ABC, LaunchConfig, DCCProcess
    connect_launcher.py    ConnectLauncher: launch via ftrack connect plugins
    fixtures.py            pytest fixtures (dcc_launcher, dcc_process, dcc_client, dcc_ui)
    plugin.py              pytest plugin with --dcc-* CLI options

tests/
    test_protocol.py       Protocol + client unit tests (no DCC needed)
    maya/
        conftest.py        Maya scene-reset fixture
        test_smoke.py      Connection, commands, MEL, scene isolation
        test_ui.py         Widget inspection, menus, callbacks
        test_ftrack_integration.py  ftrack packages, bootstrap, menu, session, dialogs
```

## Custom launchers

If you don't have an ftrack integration project, or need custom launch behavior, override the `dcc_launcher` fixture in your `conftest.py`:

```python
# tests/conftest.py
import os
import subprocess
import tempfile

import pytest

from dcc_test_harness.launcher import (
    DCCProcess,
    LaunchConfig,
    Launcher,
)


class MayaLauncher(Launcher):
    def launch(self, config: LaunchConfig) -> DCCProcess:
        maya_exe = config.dcc_executable or "/path/to/maya"
        port_file = tempfile.mktemp(suffix=".port")
        env = self._build_env(config)
        startup_code = self._build_server_startup_code(
            port_file,
            config.server_port,
            quit_fn=(
                "lambda: __import__('maya.cmds', "
                "fromlist=['cmds']).quit(force=True)"
            ),
        )
        process = subprocess.Popen(
            [maya_exe, "-command", f'python("{startup_code}")'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            port = self._wait_for_port_file(
                port_file, config.startup_timeout, process
            )
        except Exception:
            process.kill()
            raise
        finally:
            try:
                os.unlink(port_file)
            except OSError:
                pass
        return DCCProcess(
            process=process, port=port, host="127.0.0.1"
        )


@pytest.fixture(scope="session")
def dcc_launcher():
    return MayaLauncher()
```

When a `dcc_launcher` fixture is defined in your `conftest.py`, it overrides the default ConnectLauncher. The `--dcc-connect-plugin` option is not needed.

The base `Launcher` class provides three helpers:

| Helper | What it does |
|---|---|
| `_build_env(config)` | Copies `os.environ`, merges `config.extra_env`, and prepends the harness package to `PYTHONPATH`. |
| `_build_server_startup_code(port_file, port, quit_fn)` | Returns a one-liner Python string that starts the RPC server inside the DCC. |
| `_wait_for_port_file(port_file, timeout, process)` | Polls for the port file the server writes on startup. Returns the port number. |
