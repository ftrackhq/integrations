# framework-maya-deadline

Deadline Cloud extension for the ftrack Maya integration. Lives in the integrations monorepo under `projects/framework-maya-deadline/`.

## Architecture

This is NOT a standalone DCC framework plugin. It layers on top of `framework-maya` and requires it to be installed. The framework has no plugin-level extension mechanism, so this integration bootstraps independently:

1. Connect hook (priority 50, after framework-maya's 40) directly modifies `event["data"]["options"]["env"]` to inject PYTHONPATH and MAYA_SCRIPT_PATH
2. Own `userSetup.py` on `MAYA_SCRIPT_PATH` triggers deferred import
3. Bootstrap imports `get_ftrack_menu` from `ftrack_framework_maya` to create a "Deadline Cloud" submenu
4. Callbacks and dialogs are managed independently (not via the framework DCC config loop)

### Why direct env injection (not the integrations mechanism)

Connect's `_get_integrations_environments` only processes env vars from hooks whose integration name appears in the launch config's `integrations` dict. The launch config merge uses `first_level_merge` (dict.update) which replaces the `integrations` key entirely — making it impossible for an extension to add itself without overwriting framework-maya's integration list. By modifying `event["data"]["options"]["env"]` directly in the hook, we bypass this limitation entirely. This requires no changes to framework-maya.

### Callback design

- **Save**: `SceneSaved` scriptJob (post-save, non-blocking `show()` dialog, direction defaults to "Upload")
- **Open**: `MSceneMessage.kBeforeOpenCheck` via OpenMaya API (pre-open, modal `exec()` dialog, direction defaults to "Download"). Fires before Maya reads the scene file, allowing asset sync to complete before references are resolved. Returns True to proceed or False to cancel the open.
- Both callbacks open the same unified `DeadlineSyncDialog` — save in non-blocking mode, open in modal mode.
- Both are **opt-in** via toggle menu items. State persisted in Maya `optionVar`.

### Menu structure

```
Deadline Cloud
├── Sync...              → opens DeadlineSyncDialog (direction: Both)
├── ─────────
├── Sync on Save [toggle] → auto-opens dialog after save (direction: Upload)
└── Sync on Open [toggle] → auto-opens modal dialog before open (direction: Download)
```

### Scene asset tracer

The tracer has two layers:

**Shared module** (`ftrack_utils.asset_tracer` in `libs/utils/`): DCC-agnostic tracer framework. Zero new dependencies (uses stdlib `dataclasses` and the existing `clique` dep).

- `TracedAsset` — dataclass with `paths: list[Path]`, `assets: list[TracedAsset]`, `flatten() -> list[Path]`. Same schema as `ftrack-deadline-assets` but using dataclasses not pydantic.
- `BaseTracer` — ABC: `get_dependencies(cls, path: Path) -> list[Path]`
- `TraceController` — recursive tracing with cycle detection (ancestor list). Registry-based dispatch: DCC plugins call `register_tracer([".ma"], MayaFileTracer)` at import time. Two entry points: `trace(path)` for headless, `trace_live(scene_path, deps)` for DCC plugins.
- `DirectoryTracer` / `TextureTracer` — built-in file-type tracers using `clique`.

**Maya tracers** (`ftrack_framework_maya_deadline.tracer`):

- `MayaSceneTracer` — queries the live scene via `maya.cmds`. Returns only **direct** (non-referenced) deps so the controller can recurse into references without double-counting. Uses `cmds.referenceQuery(node, filename=True)` to detect referenced nodes.
- `MayaFileTracer` — headless `.ma` regex parser implementing `BaseTracer`. Handles multi-line `file -r` commands (with `re.DOTALL`), `setAttr` patterns for textures/alembic/gpuCache/imagePlane/audio. Resolves relative paths against the `.ma` file's parent directory.
- `.mb` files are treated as leaf nodes (can't be parsed headlessly; headless Maya deferred to future).
- The tracer `__init__.py` imports `MayaFileTracer` and registers it for `.ma` files, but does NOT import `MayaSceneTracer` (which requires `maya.cmds`). Import `MayaSceneTracer` directly from its module inside Maya.

### Deadline Cloud integration

The sync dialog connects to AWS Deadline Cloud to check which scene files are already synced to S3 and upload missing files.

**Architecture**: No ftrack AssetVersion involvement. The comparison is "local files vs S3 CAS" (content-addressable storage). Each file is hashed (XXH128) and checked against `{rootPrefix}/Data/{hash}.xxh128` via S3 HEAD request. Uploads use `S3AssetManager.upload_assets()` which also uploads manifests (useful for future job submission).

**Shared library: `ftrack_utils.aws`** (in `libs/utils/`): DCC-agnostic AWS/Deadline Cloud utilities, reusable by any DCC extension (Nuke, Houdini, etc.).

- `S3SyncManager` — two-phase sync: `prepare_sync()` hashes files and checks S3, returns `SyncPlan` that retains manifests. `upload_files()` uploads from that plan without re-hashing.
- `SyncPlan` / `SyncFileEntry` / `UploadResult` / `ProgressInfo` — dataclass models. `SyncPlan.to_display_dict()` returns the M4-compatible format for `SyncStatusWidget`.
- `deadline.py` — stateless functions: `get_configured_defaults()`, `list_farms()`, `list_queues()`, `get_queue_settings()`, `get_queue_session()`, `get_deadline_boto3_session()`.
- Optional dependency: `pip install ftrack-utils[aws]` pulls in `deadline` and `boto3`.

**Authentication**: Relies on Deadline Cloud Monitor being configured. `get_boto3_session()` from the deadline SDK reads `~/.deadline/config`. Verified against `ftrack-test farm` / `ftrack-test-queue` on `ftracktest-bucket-3452567690`.

**Key classes:**
- `DeadlineSyncDialog` (`dialogs/sync_dialog.py`) — unified dialog for all entry points. Constructor params: `scene_path` (explicit path for pre-open), `modal` (True for pre-open Continue/Cancel), `direction` ("upload"/"download"/"both"). Two-step flow: Compare (trace + hash + S3 check) then Sync (upload). Progress bar + cancel button during upload.
- `DeadlineWrapper` (`wrappers/deadline.py`) — thin facade over `ftrack_utils.aws`. Lazy boto3 session, delegates config/discovery/sync to shared library. Caches `SyncPlan` from Compare for the Upload step.
- `FarmQueueSelector` (`dialogs/widgets/farm_queue_selector.py`) — cascading QComboBox dropdowns, async loading via QThread workers, pre-selects from deadline config defaults
- `SyncStatusWidget` (`dialogs/widgets/sync_status_widget.py`) — summary + QTreeWidget grouped by "Needs Upload" / "Already Synced". `set_upload_complete()` shows upload stats.
- Workers (`dialogs/widgets/workers.py`) — `FarmLoadWorker`, `QueueLoadWorker`, `SyncCheckWorker`, `SyncUploadWorker` (QObject + moveToThread pattern). `SyncUploadWorker` bridges SDK's `ProgressReportMetadata` to Qt signals and supports cancellation.

**Threading model**: `MayaSceneTracer.trace()` runs on the main thread (requires `maya.cmds`). All AWS calls (farm/queue listing, file hashing, S3 checks, uploads) run off the main thread via QThread workers.

### Build system note

The build system derives `DCC_NAME` from `PROJECT_NAME.split("-")[-1]` which gives `"deadline"`. The `extensions/deadline.yaml` stub exists to satisfy this. No launch config is needed or provided (it would cause a warning about missing `identifier` field).

## Key conventions

- Python package: `ftrack_framework_maya_deadline`
- Connect hook name: `framework-maya-deadline`
- Naming pattern: `framework-{dcc}-{extension}` (enables `framework-maya-foo`, `framework-nuke-deadline`, etc.)
- Own PySide6/shiboken6 fallback in `utils.py` (does not import from framework-maya internals)
- Follows framework-maya patterns for logging and menu creation

## Building

The project uses `requires-python = ">= 3.11"` because it runs inside Maya's embedded Python 3.11. The venv must use Python 3.11 so that compiled C extensions (xxhash, pyyaml, markupsafe, charset-normalizer) get the correct `cpython-311` wheels. The lockfile is universal — use `uv lock --python 3.13` since ftrack-connect (test dep) requires `>= 3.13` for resolution.

```bash
cd projects/framework-maya-deadline
uv venv --python 3.11          # only needed once
uv lock --python 3.13          # universal lockfile covering 3.11 runtime + 3.13 test deps
uv sync --extra ftrack-libs --extra framework-libs --extra test
uv build
uv run python ../../tools/build.py --platform_dependent --include_resources resource/bootstrap build_connect_plugin .
```

Deploy the built `dist/ftrack-framework-maya-deadline-X.Y.Z/` directory to the Connect plugin path (e.g., `~/Documents/ftrack_connect_plugins/`).

## Testing

Three test categories:

- **Headless tests** (no Maya, fast): `test_file_tracer.py` and `test_deadline_wrapper.py` use `importlib` to import modules directly from their file paths, bypassing the main package `__init__.py` (which imports `maya.cmds`). Run with `uv run python -m pytest tests/test_file_tracer.py tests/test_deadline_wrapper.py -k "not deadline_cloud"`.
- **Integration tests** (`@pytest.mark.deadline_cloud`): real Deadline Cloud API tests in `test_deadline_wrapper.py`. Require AWS credentials and a configured Deadline Cloud instance. Run with `uv run python -m pytest -m deadline_cloud`.
- **Live tests** (dcc-test-harness): `test_smoke.py`, `test_callbacks.py`, `test_tracer.py`, `test_fixture_validation.py`, `test_sync_dialog.py`. The validation tests extend `ftrack_utils.__path__` inside Maya so the new `asset_tracer` subpackage is found even if the bundled ftrack-utils doesn't include it yet.

Live tests run via `dcc-test-harness` from its repo, using multiple `--dcc-connect-plugin` flags:

```bash
cd /path/to/dcc-test-harness
uv run python -m pytest /path/to/framework-maya-deadline/tests/ -v \
    --dcc-connect-plugin /path/to/framework-maya/dist/ftrack-framework-maya-X.Y.Z \
    --dcc-connect-plugin /path/to/framework-maya-deadline
```

The first plugin is the primary (provides Maya launch config). The second is layered on top (source layout supported — adds `source/` to PYTHONPATH automatically).

Shared module tests live in `libs/utils/tests/test_asset_tracer.py`.

## Dependencies

- Runtime: `ftrack-python-api`, `deadline` (AWS Deadline Cloud SDK), `boto3` (AWS SDK), `xxhash` (file hashing for S3 CAS), `ftrack-utils` (for `asset_tracer` module), framework libs (`ftrack-constants`, `ftrack-framework-core`)
- Optional: `pydantic` (deadline-extras)
- Test: `dcc-test-harness[test]` (with `ftrack-connect` override to resolve version conflicts)
