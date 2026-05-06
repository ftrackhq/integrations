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

- **Save**: `SceneSaved` scriptJob (post-save, non-blocking `show()` dialog)
- **Open**: `MSceneMessage.kBeforeOpenCheck` via OpenMaya API (pre-open, modal `exec()` dialog). Fires before Maya reads the scene file, allowing asset sync to complete before references are resolved. Returns True to proceed or False to cancel the open.
- Both callbacks are **opt-in** via toggle menu items. State persisted in Maya `optionVar`.

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

### Build system note

The build system derives `DCC_NAME` from `PROJECT_NAME.split("-")[-1]` which gives `"deadline"`. The `extensions/deadline.yaml` stub exists to satisfy this. No launch config is needed or provided (it would cause a warning about missing `identifier` field).

## Key conventions

- Python package: `ftrack_framework_maya_deadline`
- Connect hook name: `framework-maya-deadline`
- Naming pattern: `framework-{dcc}-{extension}` (enables `framework-maya-foo`, `framework-nuke-deadline`, etc.)
- Own PySide6/shiboken6 fallback in `utils.py` (does not import from framework-maya internals)
- Follows framework-maya patterns for logging and menu creation

## Building

```bash
cd projects/framework-maya-deadline
uv build
cd ../..
uv run python tools/build.py --include_resources resource/bootstrap build_connect_plugin projects/framework-maya-deadline
```

Deploy the built `dist/ftrack-framework-maya-deadline-X.Y.Z/` directory to `FTRACK_CONNECT_PLUGIN_PATH`.

## Testing

Tests run via `dcc-test-harness` from its repo, using multiple `--dcc-connect-plugin` flags:

```bash
cd /path/to/dcc-test-harness
uv run python -m pytest /path/to/framework-maya-deadline/tests/ -v \
    --dcc-connect-plugin /path/to/framework-maya/dist/ftrack-framework-maya-X.Y.Z \
    --dcc-connect-plugin /path/to/framework-maya-deadline
```

The first plugin is the primary (provides Maya launch config). The second is layered on top (source layout supported — adds `source/` to PYTHONPATH automatically).

## Testing

Two test categories:

- **Headless tests** (no Maya, fast): `test_file_tracer.py` uses `importlib` to import `MayaFileTracer` directly from its module file, bypassing the main package `__init__.py` (which imports `maya.cmds`). Run with `uv run python -m pytest tests/test_file_tracer.py`.
- **Live tests** (dcc-test-harness): `test_smoke.py`, `test_callbacks.py`, `test_tracer.py`, `test_fixture_validation.py`. The validation tests extend `ftrack_utils.__path__` inside Maya so the new `asset_tracer` subpackage is found even if the bundled ftrack-utils doesn't include it yet.

Shared module tests live in `libs/utils/tests/test_asset_tracer.py`.

## Dependencies

- Runtime: `ftrack-python-api`, `ftrack-utils` (for `asset_tracer` module), framework libs (`ftrack-constants`, `ftrack-framework-core`)
- Later milestones add: `deadline`, `boto3`, `xxhash`, `pydantic`
- Test: `dcc-test-harness[test]` (with `ftrack-connect` override to resolve version conflicts)
