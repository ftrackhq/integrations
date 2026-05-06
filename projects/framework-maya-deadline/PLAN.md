# framework-maya-deadline: Deadline Cloud Extension for Framework-Maya

## Context

Separately-installable Connect plugin that loads alongside `framework-maya` inside Maya. Registers save/open callbacks that open dialogs, allowing artists to trace scene dependencies and sync them to AWS Deadline Cloud / S3.

**Key design constraints:**
- The framework's DCC config mechanism (`registry.get_one(name='framework-maya')`) only loads a single config. The override mechanism (`first_level_merge`) replaces top-level keys, making it impossible for an extension to add itself to the integrations list without overwriting the original.
- The Connect hook therefore bypasses the integrations mechanism entirely — it directly modifies `event["data"]["options"]["env"]` to inject PYTHONPATH and MAYA_SCRIPT_PATH into the subprocess environment.

**Reference repos:**
- `ftrack-deadline-assets` — production tracer, S3 upload, ftrack publish patterns
- `fp-deadline-cloud-sync` — POC tracer, path classification, staggered sync
- `deadline-cloud-job-monitor-connect-widget` — Connect plugin packaging pattern

**Linear:** F-959

---

## Milestone 1: Project Scaffold + Connect Hook [DONE]

**Goal:** Project structure, Connect hook, bootstrap, "Deadline Cloud" submenu, test infrastructure.

### What was built

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package config with ftrack/framework/deadline dependency groups |
| `connect-plugin/hook/discover_ftrack_maya_deadline.py` | Hook at priority 50. Modifies `event["data"]["options"]["env"]` directly (PYTHONPATH + MAYA_SCRIPT_PATH) |
| `resource/bootstrap/userSetup.py` | `cmds.evalDeferred('import ftrack_framework_maya_deadline', lp=True)` |
| `source/ftrack_framework_maya_deadline/__init__.py` | Logging setup + `bootstrap()` that creates "Deadline Cloud" submenu via `get_ftrack_menu` |
| `extensions/deadline.yaml` | Stub DCC config for the build system (`DCC_NAME = PROJECT_NAME.split("-")[-1]`) |
| `tests/test_smoke.py` | 3 tests: module importable, ftrack menu exists, submenu exists |
| `README.md`, `CLAUDE.md` | Documentation |

### dcc-test-harness changes

- `--dcc-connect-plugin` now supports multiple values (`action="append"`)
- `ConnectLauncher` accepts `extra_plugins` parameter
- `_apply_extra_plugin_env()` probes well-known dirs (dependencies/, source/, resource/bootstrap/) without requiring a launch config
- Source layout: adds `source/` to PYTHONPATH for dev mode

### Key decisions

- **Direct env injection**: Hook modifies `event["data"]["options"]["env"]` instead of returning `launch_data["integration"]["env"]`. Bypasses Connect's integrations mechanism and its `first_level_merge` ordering issues. Requires no changes to framework-maya.
- **No launch config**: The extension doesn't need one. A launch config with `name: framework-maya` would trigger `first_level_merge` which replaces the `integrations` key. An incomplete one causes a Connect warning about missing `identifier`.
- **Menu**: Submenu under ftrack menu via `get_ftrack_menu(submenu_name='Deadline Cloud')` imported from `ftrack_framework_maya`.
- **ftrack session**: Deferred to M4 (M1 only needs `maya.cmds`).

---

## Milestone 2: Callbacks + Dialog Shells [DONE]

**Goal:** Opt-in save/open callbacks, placeholder dialogs, menu items.

### What was built

| File | Purpose |
|------|---------|
| `source/.../utils.py` | PySide6/shiboken6 fallback + `get_maya_main_window()` |
| `source/.../callbacks.py` | Save: SceneSaved scriptJob. Open: `MSceneMessage.kBeforeOpenCheck`. Opt-in toggles via `optionVar`. Dialog singletons. |
| `source/.../dialogs/save_dialog.py` | "Deadline Cloud - Publish" shell (non-blocking `show()`) |
| `source/.../dialogs/open_dialog.py` | "Deadline Cloud - Scene Status" shell. Accepts `scene_path`. Modal (`exec()`) with Continue/Cancel when triggered by kBeforeOpenCheck. |
| `source/.../__init__.py` | Extended bootstrap: 4 menu items + restore callbacks from prefs |
| `tests/test_callbacks.py` | 10 tests: menu items, toggles on/off, dialogs open, save-triggered dialog, singleton |

### Key decisions

- **Opt-in via menu toggle**: "Sync on Save" and "Sync on Open" checkBox menuItems. State in `optionVar` (`ftrack_deadline_sync_on_save`, `ftrack_deadline_sync_on_open`). Default: disabled.
- **Pre-open callback**: `MSceneMessage.kBeforeOpenCheck` (not SceneOpened scriptJob). Fires before Maya reads the scene, blocking until the modal dialog closes. Returns True to proceed or False to cancel. This ensures assets can be synced before Maya resolves references.
- **Post-save callback**: `SceneSaved` scriptJob with `evalDeferred`. Non-blocking.
- **Two separate dialogs**: `DeadlineSaveDialog` (publish flow) and `DeadlineOpenDialog` (download flow). Each evolves independently.
- **Own utils.py**: PySide6/shiboken6 fallback, no import from framework-maya internals.
- **Dialog singleton**: Module-level references avoid stacking on rapid saves. Reuses visible instance if still open.

---

## Milestone 3: Scene Asset Tracer [DONE]

**Goal:** DCC-agnostic asset tracer with Maya-specific implementations for live scene queries and headless `.ma` file parsing.

### What was built

**Shared library: `ftrack_utils.asset_tracer`** (in `libs/utils/`)

| File | Purpose |
|------|---------|
| `asset_tracer/__init__.py` | Exports: TracedAsset, BaseTracer, TraceController |
| `asset_tracer/models.py` | `TracedAsset` dataclass (paths, assets, flatten()) |
| `asset_tracer/base.py` | `BaseTracer` ABC with `get_dependencies(path) -> list[Path]` |
| `asset_tracer/controller.py` | `TraceController`: registry, recursive tracing, cycle detection |
| `asset_tracer/tracers.py` | `DirectoryTracer` (clique), `TextureTracer` (UDIM expansion) |

**Maya tracers** (in `projects/framework-maya-deadline/`)

| File | Purpose |
|------|---------|
| `tracer/__init__.py` | Re-exports, registers MayaFileTracer for `.ma` files |
| `tracer/maya_scene_tracer.py` | `MayaSceneTracer`: live scene tracing via `maya.cmds` |
| `tracer/maya_file_tracer.py` | `MayaFileTracer`: headless `.ma` regex parser |

**Test fixtures** (13 `.ma` files in `tests/fixtures/`)

### Key decisions

- **DCC-agnostic, not deadline-specific**: The tracer lives in `ftrack_utils.asset_tracer`, reusable by any integration. Not coupled to Deadline Cloud.
- **dataclasses, not pydantic**: Avoids adding a heavy dependency to ftrack-utils. API-compatible with `ftrack-deadline-assets` TracedAsset schema.
- **clique, not pyseq**: Uses the existing ftrack-utils dependency for sequence detection. Zero new dependencies.
- **Registry pattern**: `TraceController.register_tracer()` replaces hardcoded if-chains. DCC plugins register their file tracers at import time.
- **Mixed live + headless**: `MayaSceneTracer` queries `maya.cmds` for the current scene (non-referenced nodes only). `MayaFileTracer` parses `.ma` files headlessly. The controller recursively follows references.
- **`.mb` files as leaf nodes**: Can't be parsed headlessly. Future: headless Maya instance. 
- **UDIM fallback**: When TextureTracer can't expand (directory doesn't exist), the original UDIM path is preserved as a leaf node.
- **Reference filtering**: `_is_referenced()` uses `cmds.referenceQuery()` to skip nodes from referenced scenes, preventing double-counting.

### Test counts

- 15 shared module tests (`libs/utils/tests/test_asset_tracer.py`) — TracedAsset model, controller dispatch, recursion, cycle detection
- 16 headless parser tests (`tests/test_file_tracer.py`) — all fixture types, recursive tracing, cycle detection, .mb leaf
- 9 live scene tests (`tests/test_tracer.py`) — empty/unsaved scene, textures, references, audio, image planes, reference filtering
- 22 fixture validation tests (`tests/test_fixture_validation.py`) — loads each fixture in Maya, compares live vs headless tracer output, verifies reference filtering

Total: 62 new tests (13 existing from M1-M2 = 75 total)

---

## Milestone 4: Compare Dialog + Deadline Cloud Integration [PLANNED]

**Goal:** Wire save dialog to trace, compare against S3 manifests, show change summary. Farm/queue selection.

### Deliverables
- Fully functional `DeadlineSaveDialog` with farm/queue dropdowns, compare button, results panel
- `DeadlineWrapper` for AWS auth, S3 ops, manifest comparison
- `FtrackWrapper` for session helpers

---

## Milestone 5: Publish (S3 Upload + ftrack AssetVersion) [PLANNED]

**Goal:** Full publish: trace -> hash (XXH128) -> upload S3 -> create manifests -> create ftrack AssetVersion with scene + inputManifest components.

### Publish flow
1. Trace via MayaTracer
2. Expand sequences
3. Get queue S3 settings
4. Hash all files (XXH128), create local manifest
5. Upload to S3 (content-addressable: `{root}/Data/{hash}.xxh128`)
6. Upload manifest to S3
7. Create ftrack AssetVersion with components
8. Display success

---

## Milestone 6: Open Dialog, Download, and Polish [PLANNED]

**Goal:** Pre-open dialog detects published versions, offers download of changed files. Config persistence, error handling.

### Deliverables
- `DeadlineOpenDialog` with version detection, quick/deep compare, download
- `optionVar` persistence for farm/queue selection
- Error handling: no network, expired AWS creds, missing files

---

## Milestone Dependency Graph

```
M1: Scaffold + Hook [DONE]
 |
 +---> M2: Callbacks + Dialog Shells [DONE]
 |         |
 +---> M3: Scene Asset Tracer [DONE]
 |         |
 +---- M4: Compare Dialog (requires M2 + M3)
           |
           M5: Publish (requires M4)
           |
           M6: Open + Download + Polish (requires M5)
```

---

## Test Infrastructure

Tests run from the `dcc-test-harness` repo using multiple `--dcc-connect-plugin` flags:

```bash
cd /path/to/dcc-test-harness
uv run python -m pytest /path/to/framework-maya-deadline/tests/ -v \
    --dcc-connect-plugin /path/to/framework-maya/dist/ftrack-framework-maya-X.Y.Z \
    --dcc-connect-plugin /path/to/framework-maya-deadline
```

First plugin = primary (Maya discovery). Second = layered on top.

Test markers:
- `@pytest.mark.deadline_cloud` — requires AWS credentials (M4-M6)
- All M1-M2 tests run without external services

Current test count: 75 (3 smoke + 10 callbacks + 15 shared asset_tracer + 16 headless parser + 9 live tracer + 22 fixture validation).
Headless tests (31) run with plain pytest. Live tests (44) run via dcc-test-harness.

---

## Key Patterns Reused

| Pattern | Source |
|---------|--------|
| Connect hook structure | `framework-maya/connect-plugin/hook/` |
| Bootstrap via `userSetup.py` | `framework-maya/resource/bootstrap/` |
| `get_ftrack_menu(submenu_name=)` | `framework-maya/__init__.py:60-85` |
| `TraceController` + tracers | `ftrack-deadline-assets/.../tracer/` |
| `TracedAsset` model | `ftrack-deadline-assets/.../tracer/models.py` |
| `DeadlineWrapper` (S3, hashing) | `ftrack-deadline-assets/.../wrappers/deadline.py` |
| `FtrackWrapper` (AssetVersion) | `ftrack-deadline-assets/.../wrappers/ftrack.py` |
| Qt dialog parented to Maya | `shiboken6.wrapInstance` + `MQtUtil.mainWindow()` |
