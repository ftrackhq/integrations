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
- **Own utils.py**: PySide6/shiboken6 fallback, no import from framework-maya internals.
- **Dialog singleton**: Module-level reference avoids stacking on rapid saves. Reuses visible instance if still open.

*Note: M2 originally built two separate dialog shells (save + open). These were merged into a single `DeadlineSyncDialog` in M4.*

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

## Milestone 4: Compare Dialog + Deadline Cloud Integration [DONE]

**Goal:** Wire save dialog to trace, hash files, check S3 sync status, show results. Farm/queue selection.

**Key architectural decision:** No ftrack AssetVersion involvement. The extension handles file sync to S3 CAS (content-addressable storage). ftrack publishing happens through the normal framework-maya workflow. Manifests are a job-submission concern (created at render time), not a sync concern.

### What was built

| File | Purpose |
|------|---------|
| `source/.../wrappers/__init__.py` | Re-exports DeadlineWrapper |
| `source/.../wrappers/deadline.py` | Lazy boto3 session, farm/queue listing, S3 sync check via S3AssetManager + S3AssetUploader |
| `source/.../dialogs/widgets/workers.py` | QThread workers: FarmLoadWorker, QueueLoadWorker, SyncCheckWorker |
| `source/.../dialogs/widgets/farm_queue_selector.py` | Cascading farm/queue dropdowns with async loading and config defaults |
| `source/.../dialogs/widgets/sync_status_widget.py` | Summary labels + QTreeWidget grouped by "Needs Upload" / "Already Synced" |
| `source/.../dialogs/sync_dialog.py` | Unified sync dialog replacing save/open shells. Direction selector (Upload/Download/Both), modal mode for pre-open callback |
| `tests/test_deadline_wrapper.py` | 8 mocked headless tests + 4 integration tests (deadline_cloud marker) |
| `tests/test_sync_dialog.py` | 12 live Maya dialog tests |

### Key decisions

- **No ftrack AssetVersion**: Comparison is "local files vs S3 CAS", not "current vs previous version". Hash each file (XXH128), check if `{rootPrefix}/Data/{hash}.xxh128` exists via S3 HEAD request. Binary per file: "needs upload" vs "already synced".
- **No manifests for comparison**: Manifests are created transiently during hashing (by `S3AssetManager.hash_assets_and_create_manifest()`) but are not uploaded to S3. Manifest upload is a job-submission concern.
- **Unified dialog**: Merged save/open dialogs into single `DeadlineSyncDialog`. Direction selector (Upload/Download/Both) sits next to the Sync button. Modal mode (Continue/Cancel) for pre-open callback, non-blocking for menu/save. Menu simplified to one "Sync..." entry plus toggles.
- **Direction defaults**: Menu opens with "Both", save callback with "Upload", pre-open callback with "Download".
- **Deadline Cloud Monitor for auth**: `get_boto3_session()` from the deadline SDK reads credentials configured by the Deadline Cloud Monitor desktop app. No custom auth flow.
- **deadline + boto3 as core dependencies**: Moved from optional `deadline-libs` group to core `dependencies` in pyproject.toml so they're included in the built dist.
- **Lazy wrapper init**: DeadlineWrapper created on first dialog interaction, not at construction. If SDK unavailable, a stub is used and an error is shown inline.
- **QThread workers**: All AWS I/O runs off Maya's main thread. Scene tracing (fast, `maya.cmds` queries) runs on main thread, then SyncCheckWorker handles hashing + S3 checks.
- **importlib pattern for headless tests**: Tests import the wrapper module directly via `importlib` to bypass the package `__init__.py` (which imports `maya.cmds`).

### Test counts

- 8 headless mocked tests (`tests/test_deadline_wrapper.py`)
- 4 integration tests (`@pytest.mark.deadline_cloud`, verified against `ftrack-test farm`)
- 12 live Maya dialog tests (`tests/test_sync_dialog.py`)

Total: 24 new tests (31 existing headless + 44 existing live = 99 total project tests)

---

## Milestone 5: Sync (S3 Upload) [PLANNED]

**Goal:** Upload missing files to S3 CAS. No ftrack AssetVersion, no manifest upload — just push file content so it's pre-staged for future Deadline Cloud job submissions.

### Sync flow
1. Reuse M4's trace + hash + S3 check
2. Upload files not yet on S3 to `{rootPrefix}/Data/{hash}.xxh128`
3. Show progress (bytes uploaded, transfer rate)
4. Display success summary

---

## Milestone 6: Open Dialog, Download, and Polish [PLANNED]

**Goal:** Pre-open dialog detects synced files, offers download. Config persistence, error handling.

### Deliverables
- `DeadlineOpenDialog` with S3 status detection, download
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
 +---- M4: Compare Dialog + Deadline Cloud [DONE]
           |
           M5: Sync / S3 Upload (requires M4)
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

Current test count: 99 (3 smoke + 10 callbacks + 15 shared asset_tracer + 16 headless parser + 9 live tracer + 22 fixture validation + 8 deadline wrapper mocked + 4 deadline wrapper integration + 12 sync dialog).
Headless tests (39) run with plain pytest. Live tests (56) run via dcc-test-harness. Integration tests (4) require `@pytest.mark.deadline_cloud`.

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
| Qt dialog parented to Maya | `shiboken6.wrapInstance` + `MQtUtil.mainWindow()` |
