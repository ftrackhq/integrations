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

- A **JavaScript package** (`resource/bootstrap/js/`) is deployed into
  Harmony's scripts folder and loaded at startup. It runs a small TCP
  **server** inside Harmony's Qt Script environment, builds the ftrack
  menu, and executes DCC commands (e.g. rendering an image sequence)
  on request.
- A **standalone Python process** (`ftrack_framework_harmony`) runs the
  ftrack framework (Host, Client, Qt UI). It is the TCP **client**: it
  connects to Harmony, sends the tool list so the menu can be built,
  and shows the publisher dialog.

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

Minimally functional: launch, ftrack menu, and a standard publisher that
exports an image sequence, a reviewable movie and a thumbnail. Opener,
loader and asset-manager workflows are deferred (see the release notes).

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
  extension registry was scanned and the TCP link to Harmony is live.
  Requires ftrack credentials (`FTRACK_SERVER`/`FTRACK_API_KEY`, or a
  prior ftrack Connect login); skipped otherwise.

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
