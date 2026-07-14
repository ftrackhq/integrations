# Framework Harmony integration

Community owned Toon Boom Harmony integration for ftrack.

## Supported versions

Toon Boom Harmony 22, 24, 25 and 27 (Premium, Advanced and Essentials
editions) on macOS and Windows. The Connect launcher discovers Harmony
`>= 22`. Validated against Harmony 27 Premium.

> The Linux script-deployment path in the launch hook is untested.

## Architecture

Harmony has no embedded Python interpreter, so the integration runs as
**two processes bridged over TCP**:

- A **standalone Python process** (`ftrack_framework_harmony`) runs the
  ftrack framework (Host, Client, Qt UI). It is the TCP **server**: it
  binds a loopback port and listens for Harmony's whole lifetime, sends
  the tool list so the menu can be built, and shows the publisher/opener
  dialogs. It monitors the Harmony process and shuts itself down when
  Harmony exits (a process watchdog), so no helper process is left
  behind.
- A **JavaScript package** (`resource/bootstrap/js/`) is deployed into
  Harmony's scripts folder and loaded at startup. It is the TCP
  **client**: it dials out to the standalone server from Harmony's Qt
  Script environment, builds the ftrack menu, and executes DCC commands
  (e.g. rendering an image sequence) on request.

Harmony tears down its Qt Script engine — and the client socket with it
— on every scene switch, but the external server outlives every switch,
so Harmony simply reconnects each time and the RPC channel never dies
with the engine.

The tools are grouped as adjacent `ftrack <Tool>` entries at the end of
the **File menu** (below Import/Export) and on a dedicated **"ftrack"
toolbar** (one button per tool). Harmony's `ScriptManager` can only add
items to existing menus; a custom top-level menu or a nested submenu
needs overriding Harmony's whole `menus.xml` (version-brittle, and a
hierarchical `targetMenuId` such as `File/ftrack` does not render on
Harmony 27). The Windows menu scatters script items (first at the top
of its view list, the rest at the bottom), so the File menu is used —
script items append there adjacently.

Harmony rebuilds the menu bar on every scene switch, dropping
script-added items, and destroys the Qt Script engine (and the client
socket). `TB_sceneOpened` and `TB_sceneCreated` hooks (deployed to the
user scripts root next to the ftrack package) re-include `configure.js`
after each scene open and create, then **(1)** re-register the ftrack
menu entries synchronously from the persisted tool list (so the menu is
back immediately, not gated on the network) and **(2)** **reconnect** to
the standalone server, which restores the RPC channel (so the menu
actions work) and re-sends its tool list to rebuild the menu once more.
The toolbar and shortcut persist across scene switches, so the whole
surface stays present and clickable across File > Open, File > New,
close-and-reopen and the ftrack Open tool. Each hook **chains** Harmony's
default
callback of the same name — it `include`s the default from
`specialFolders.resource/scripts/`, keeps a reference and calls it
first, so Harmony's standard behaviour (e.g. the default
`TB_sceneCreated` builds the new scene's nodes and frame range) is
preserved. The deploy never overwrites a studio's own hook of the same
name (ours carry an `[ftrack]` marker).

ftrack Connect starts both when Harmony is launched: it runs the DCC
and, because the launch config declares
`standalone_module: ftrack_framework_harmony`, also spawns the
standalone helper process. The connect-plugin hook
(`connect-plugin/hook/discover_ftrack_framework_harmony.py`) deploys the
JS package to
`<prefs>/Toon Boom Animation/Toon Boom Harmony <variant>/<version>00-scripts/packages/ftrack/`
on every launch and sets the environment the two processes share
(`FTRACK_INTEGRATION_LISTEN_PORT`,
`FTRACK_REMOTE_INTEGRATION_SESSION_ID`, `FTRACK_HARMONY_VERSION`).

The interaction model still relies on Harmony's Qt Script engine and the
`packages`/`configure.js` mechanism, both of which remain current
through Harmony 27. Toon Boom's newer external Python API
(`from ToonBoom import harmony`, Harmony 24+) is a possible future
alternative for the command surface — see the release notes for the
deferred spike.

## Functionality

- **Publish** a standard publisher exporting an image sequence, a
  reviewable movie, a thumbnail, and a **scene snapshot** (the Harmony
  scene folder zipped as a `snapshot` component).
- **Open** a published scene snapshot back into the running Harmony
  session (`scene.closeSceneAndOpenOffline`).

Loader and asset-manager workflows are deferred (see the release notes).
Opening a scene closes the current one — it does not prompt to save
first (a future improvement). The scene snapshot currently zips the
whole scene folder, including any cached frames.

## Building

### Preparations

Install uv.

Create and activate a project-local virtual environment:

```bash
cd projects/framework-harmony
uv venv .venv
source .venv/bin/activate
```

Update release notes.

Set version in `pyproject.toml` (use semantic versioning, for example
`MAJOR.MINOR.PATCH` or prerelease `MAJOR.MINOR.PATCHrcN`).

Tag and push to SCM.

### CI build

See Monorepo build CI.

### Manual build

Build with uv:

```bash
    uv build
```

Build Connect plugin:

```bash
    cd projects/framework-harmony
    uv run python ../../tools/build.py --include_resources resource/bootstrap build_connect_plugin .
```

If the build fails and Harmony is using beta or experimental
dependencies published to Test PyPi, use the `--testpypi` flag to build
the plugin.

To build from source, not involving PyPi, use the `--from_source` flag.

## Testing

The automated tests launch a locally installed Harmony through the same
launch config Connect uses, deploy the JS package via the hook, and
verify the integration loads. They use the
[`dcc-test-harness`](../../libs/dcc-test-harness) library and are skipped
when Harmony is not installed.

Install the test dependencies from the project directory:

```bash
cd projects/framework-harmony
uv sync --extra ftrack-libs --extra framework-libs --extra test
```

Run against the source project:

```bash
uv run pytest tests/ --dcc-connect-plugin .
```

Or against a built Connect plugin (closest to production):

```bash
uv run pytest tests/ --dcc-connect-plugin dist/ftrack-framework-harmony-<version>
```

The suite has two tiers:

- **`tests/test_launch.py`** launches Harmony, deploys the JS package,
  and drives the TCP wire protocol from the test process to verify the
  package loads, the menu handshake completes, and RPC round-trips
  reach Harmony's scripting API. No ftrack server needed.
- **`tests/test_standalone.py`** additionally spawns the real standalone
  framework process (as Connect does) and asserts, via the harness'
  in-process server, that the ftrack session/Host/Client came up, the
  extension registry was scanned, the TCP link to Harmony is live, and
  the scene save/open commands round-trip. Requires ftrack credentials
  (`FTRACK_SERVER`/`FTRACK_API_KEY`, or a prior ftrack Connect login);
  skipped otherwise.
- **`tests/test_process_cleanup.py`** kills Harmony and asserts the
  standalone helper process exits (the cleanup watchdog). Also requires
  credentials.

The full publish-to-ftrack and opener-dialog round trip is verified
manually (it needs real server data).

macOS notes: launching Harmony requires that no other Harmony instance
is running (a second instance fails its license check). On a trial
install the launcher dismisses the "Continue Trial" dialog and creates
a temporary scene via accessibility automation, which needs the test
runner (terminal/IDE) to be granted **Accessibility** permission in
System Settings > Privacy & Security.

## Installing

### Connect plugin

Copy the resulting `dist/ftrack-framework-harmony-<version>` folder to
your Connect plugin folder.
