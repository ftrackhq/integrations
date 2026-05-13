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

## Milestone 5: Sync (S3 Upload) [DONE]

**Goal:** Upload missing files to S3 CAS via `S3AssetManager.upload_assets()`. Extract DCC-agnostic sync logic into `ftrack_utils.aws` for reuse.

### What was built

**Shared library: `ftrack_utils.aws`** (in `libs/utils/`)

| File | Purpose |
|------|---------|
| `aws/__init__.py` | Public API exports |
| `aws/models.py` | `SyncPlan`, `SyncFileEntry`, `UploadResult`, `ProgressInfo` dataclasses |
| `aws/deadline.py` | Stateless functions: config defaults, farm/queue discovery, session mgmt |
| `aws/s3_sync.py` | `S3SyncManager`: `prepare_sync()` + `upload_files()` |

**Maya integration updates** (in `projects/framework-maya-deadline/`)

| File | Purpose |
|------|---------|
| `wrappers/deadline.py` | Refactored: thin facade over `ftrack_utils.aws`, caches `SyncPlan` |
| `dialogs/widgets/workers.py` | Added `SyncUploadWorker` with progress + cancellation |
| `dialogs/sync_dialog.py` | Wired Sync button, progress bar, cancel button, upload flow |
| `dialogs/widgets/sync_status_widget.py` | Added `set_upload_complete()` |

### Key decisions

- **Two-phase design**: `prepare_sync()` returns a `SyncPlan` retaining manifests. `upload_files()` reuses them — no re-hashing after Compare.
- **Manifests uploaded with content**: `upload_assets()` handles both atomically. Manifests are useful for future job submission.
- **Cancellation via SDK callback**: `SyncUploadWorker` bridges the SDK's `ProgressReportMetadata` callback (return False to cancel → `AssetSyncCancelledError`).
- **Optional deps**: `ftrack-utils[aws]` extra pulls in `deadline>=0.49.0` + `boto3>=1.35.0`.
- **Backward-compatible**: `check_sync_status()` returns the same dict as M4 (via `SyncPlan.to_display_dict()`).

### Test counts

- 24 shared module tests (`libs/utils/tests/test_aws.py`) — models, S3SyncManager, deadline functions
- 12 headless wrapper tests (`tests/test_deadline_wrapper.py`) — 8 existing (updated) + 4 new upload tests
- 7 new live dialog tests (`tests/test_sync_dialog.py`) — sync button, progress bar, cancel button, upload complete

Total: 43 new tests (56 existing headless + 56 existing live = 155 total)

---

## M5 post-work: Build + Callback + Auth fixes [DONE]

Fixes applied after M5 integration testing.

### What was built

| Change | Details |
|--------|---------|
| Python 3.11 build support | Relaxed `requires-python` to `>= 3.11` on monorepo libs (constants, utils, framework-core) and dcc-test-harness so compiled extensions (xxhash, pyyaml, markupsafe) get `cpython-311` wheels matching Maya 2026's Python. Project venv uses 3.11; lockfile is universal via `uv lock --python 3.13`. |
| xxhash as core dep | Moved from `deadline-extras` optional to core `dependencies`. Required for S3 CAS file hashing. |
| S3AssetUploader SDK fix | deadline SDK 0.56.1 added required kwargs `s3_max_pool_connections` and `small_file_threshold_multiplier` to `S3AssetUploader.__init__()`. Added with defaults (50, 20). |
| Pre-open callback fix | Maya API 2.0 check callbacks use `(fileObject, clientData)` signature with return value, not `(retCode, fileObject, clientData)`. Fixed signature and explicit `clientData=None` in registration. |
| Headless tracing for pre-open | Compare flow uses `TraceController.trace(Path)` (headless `MayaFileTracer`) when `_explicit_scene_path` is set (pre-open), `MayaSceneTracer.trace()` (live) otherwise. |
| Auto-login on credential errors | `is_credential_error()` in `ftrack_utils.aws.deadline` detects `NoCredentialsError`, `PartialCredentialsError`, `CredentialRetrievalError`, and auth-related `ClientError` codes. Workers emit `credential_error` signal → dialog shows `DeadlineLoginDialog.login()` (SDK's blocking login) → on success resets wrapper and reloads farms. |

### Test counts

- 9 `is_credential_error` tests in `libs/utils/tests/test_aws.py`
- Existing headless + shared tests unchanged (12 + 33 = 45)

---

## Milestone 6: Download, Auto-Login, Persistence, Error Handling [DONE]

**Goal:** S3 CAS download via manifest matching, auto-login on credential errors, farm/queue persistence, network error handling.

### What was built

| Component | Details |
|-----------|---------|
| **S3 CAS download** | `S3SyncManager.find_manifest_for_scene(scene_hash)` — HEADs manifests in S3 to find the one tagged with the scene's XXH128 hash. `prepare_download(file_paths, scene_hash, scene_path)` — derives asset root by matching scene's absolute path against its relative manifest entry, checks all manifest files against local filesystem. `download_files(plan)` — builds synthetic manifests, calls SDK's `download_files_from_manifests()`. |
| **Scene-hash metadata** | `upload_files(scene_hash=)` stores `scene-hash` as S3 object metadata on the manifest via `copy_object` after upload. Enables deterministic manifest matching by content hash. |
| **Auto-login** | `is_credential_error()` and `is_network_error()` in `ftrack_utils.aws.deadline`. Workers emit `credential_error` signal → dialog shows `DeadlineLoginDialog.login()` (SDK's blocking login) → on success resets wrapper and reloads farms. Detects `NoCredentialsError`, `PartialCredentialsError`, `CredentialRetrievalError`, auth-related `ClientError` codes, `EndpointConnectionError`, `ConnectTimeoutError`. |
| **optionVar persistence** | `ftrack_deadline_farm_id` / `ftrack_deadline_queue_id` saved on selection change, restored before SDK defaults on load. Uses `cmds.optionVar(exists=)` to avoid `0` for unset vars. |
| **Headless tracing** | All `.ma` scenes use `TraceController.trace()` (headless `MayaFileTracer`) regardless of entry point. Finds ALL references including unresolved ones Maya skipped. |
| **Path handling** | `TraceController` preserves paths on `FileNotFoundError` (not silently dropped). Wrapper resolves `../` before passing to SDK. `prepare_sync` reconstructs absolute paths from asset root + relative manifest paths. |
| **Download UI** | `SyncDownloadWorker` with progress + cancellation. `SyncStatusWidget` shows "Needs Download" group. Direction="download" and "both" wired in dialog. Full absolute paths displayed. |
| **Models** | `DownloadResult` dataclass. `SyncPlan.needs_download` and `download_size_bytes` fields. `to_display_dict()` includes download data. |

### Test counts

- 6 sync flow tests (`TestSyncFlow` in `test_deadline_wrapper.py`) — trace + upload/download separation, path resolution, deleted ref preservation
- 4 network error tests + 9 credential error tests in `test_aws.py`
- Existing tests updated for `scene_hash` parameter

### TODO (open / deferred)

1. ~~**Automated upload/download integration tests**~~ — **DONE** (see M7 below).

2. **End-to-end pre-open test in Maya** — The full `kBeforeOpenCheck` → headless trace → compare → download → Continue → Maya opens flow hasn't been tested as a complete automated workflow. Requires manual testing with Maya + AWS credentials.

3. **"Both" direction UX** — Upload then download works sequentially, but there's no combined progress display (upload finishes, then download starts separately).

4. **Cross-machine download** — Asset root derivation assumes the scene file's relative position is the same on both machines. Different directory layouts (e.g., `/projects/show/` vs `/mnt/shared/show/`) would require path remapping — not yet addressed.

5. **dcc-test-harness `requires-python`** — Changed to `>=3.11` in the separate `dcc-test-harness` repo (`/Users/dennis.weil/code/ftrackhq/dcc-test-harness/pyproject.toml`). Needs to be committed there.

---

## Milestone 7: Automated S3 Round-Trip Integration Tests [DONE]

**Goal:** Exercise the full upload/download lifecycle against real S3 with randomised fixtures.

### What was built

| Component | Details |
|-----------|---------|
| **`test_s3_roundtrip.py`** | 6 `@pytest.mark.deadline_cloud` tests exercising `S3SyncManager` directly against real S3. Each test gets its own randomised fixture tree (via function-scoped `randomized_scene` fixture) ensuring unique CAS hashes per run. |
| **Fixture randomisation** | `_randomize_tree()` copies `fixtures/versioned/` to `tmp_path`, appends `// test-nonce: <uuid>` to `.ma` files and 32 random bytes to binary files. Original fixtures never modified. |
| **conftest fixtures** | `deadline_queue_session` (session) and `s3_sync_manager` (session) provide a pre-validated `S3SyncManager` bound to the test farm/queue. |

### Test cases

| Test | What it verifies |
|------|-----------------|
| `test_upload_all_deps` | Trace → prepare_sync → all need upload → upload succeeds |
| `test_manifest_has_scene_hash` | Upload → find_manifest_for_scene returns non-None manifest |
| `test_reupload_is_noop` | Second prepare_sync → all in already_synced, upload_size_bytes == 0 |
| `test_download_plan_detects_missing` | Upload → delete deps → prepare_download → deleted files in needs_download |
| `test_download_restores_files` | Upload → delete → download → files restored with correct hashes |
| `test_full_roundtrip` | Golden path: trace → upload → find manifest → delete → download → verify content |

### Test counts

- 6 new S3 round-trip tests in `test_s3_roundtrip.py`
- Existing integration tests unchanged (3 in `test_deadline_wrapper.py`)
- Total `@pytest.mark.deadline_cloud` tests: 9

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
           M5: Sync / S3 Upload [DONE]
           |
           M5-post: Build + Callback + Auth fixes [DONE]
           |
           M6: Download + Auto-Login + Polish [DONE]
           |
           M7: S3 Round-Trip Integration Tests [DONE]
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

Current test count: 171+ (3 smoke + 10 callbacks + 15 shared asset_tracer + 37 shared aws (incl. 9 credential + 4 network) + 16 headless parser + 9 live tracer + 22 fixture validation + 18 deadline wrapper mocked (incl. 6 sync flow) + 4 deadline wrapper integration + 6 S3 round-trip integration + 19 sync dialog + 7 upload dialog + 16 versioned sync tests).
Headless tests (102) run with plain pytest. Live tests (63+) run via dcc-test-harness. Integration tests (10) require `@pytest.mark.deadline_cloud`.

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
| `S3AssetManager.upload_assets()` | `ftrack-deadline-assets/.../wrappers/deadline.py:461` |
| `ProgressReportMetadata` callback | deadline SDK `progress_tracker.py` |
| `asset_tracer` module structure | `ftrack_utils/asset_tracer/` (model for `aws/` subpackage) |
| Qt dialog parented to Maya | `shiboken6.wrapInstance` + `MQtUtil.mainWindow()` |
