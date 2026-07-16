# Frozen Connect leaks its bundled Qt env into launched DCCs

Status: implemented

Launching a DCC through the **installed** (frozen) ftrack Connect leaks
Connect's own bundled Qt paths into the child process. On Windows,
Harmony 25.2/27 then prints ~10 `qt.core.plugin.loader: ... Plugin uses
incompatible Qt library (6.6.0) [release]` warnings and breaks (crash,
missing menus/dialogs). This records the root cause, the two-layer fix,
why an alternative patch was rejected, and the removal criteria for the
transitional layer.

## Root cause

Verified end-to-end:

1. **Installed Connect is a PyInstaller app.** PyInstaller's built-in
   PySide6 runtime hook (`pyi_rth_pyside6`) *always* overwrites
   `QT_PLUGIN_PATH` and `QML2_IMPORT_PATH` in the frozen process,
   pointing at Connect's bundled Qt (PySide6 6.6.3,
   `apps/connect/pyproject.toml`); on Windows it also *prepends*
   `sys._MEIPASS` (`...\ftrack Connect\_internal`) to `PATH`. No custom
   runtime hooks exist in the repo.
2. **Connect's launcher hands its whole environment to children.**
   `_get_application_environment`
   (`apps/connect/source/ftrack_connect/application_launcher/__init__.py`)
   does `environment = os.environ.copy()`, popping only
   `PYTHONHOME`/`FTRACK_EVENT_PLUGIN_PATH`. That dict feeds *both*
   `subprocess.Popen` calls — the DCC and the standalone framework
   helper. It is the only DCC spawn site in the repo.
3. **Harmony 25.2/27 embed Qt 6.4.2.** Qt rejects plugins built with a
   newer minor (6.6 > 6.4) → the ten warnings come from *Harmony's own
   process* scanning the leaked `QT_PLUGIN_PATH`. Leaked
   `QML2_IMPORT_PATH`/`PATH` are the plausible vector for the visible
   breakage (6.6 QML modules fail hard in a 6.4 runtime; `PATH` can
   shadow DLLs).
4. **macOS has the same leak** — a launch from the installed
   `Ftrack Connect.app` passes `QT_PLUGIN_PATH=.../Contents/Frameworks/
   PySide6/Qt/plugins` and a `QML2_IMPORT_PATH` with entries under both
   `Contents/Frameworks` *and* `Contents/Resources` to the DCC.
   Unnoticed because DCC stderr never reaches ftrack's log files and
   from-source Connect runs do not set these vars. The
   `Contents/Resources` entry is **not** under `sys._MEIPASS`
   (= `Contents/Frameworks`), so bundle-root detection must add the
   app-bundle root, not just `_MEIPASS`.

## Fix — two layers

Both land as one PR; separate release vehicles pick them up.

### Layer 1 — Connect launcher (root fix)

`apps/connect/.../application_launcher/__init__.py`. New pure,
unit-testable helpers (caller supplies bundle roots):

- `FROZEN_QT_ENVIRONMENT_VARIABLES` — `QT_PLUGIN_PATH`,
  `QT_QPA_PLATFORM_PLUGIN_PATH`, `QML_IMPORT_PATH`, `QML2_IMPORT_PATH`,
  `PATH`, `LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`.
- `get_frozen_bundle_roots()` — `[]` when not frozen; else `[_MEIPASS]`
  plus, on a macOS `.app` (`_MEIPASS` ends `Contents/Frameworks`), the
  app-bundle root.
- `strip_frozen_qt_environment(environment, bundle_roots)` — per var,
  split on `os.pathsep`, drop entries at/under any root
  (`normcase`+`normpath` textual prefix compare with an explicit
  separator guard, no `realpath`), keep foreign entries in order, re-set
  or pop. No-op for empty roots.
- `restore_loader_library_path(environment)` — Linux/frozen: restore the
  bootloader's `LD_LIBRARY_PATH_ORIG` (PyInstaller-documented pattern for
  spawning external processes).

Wired into `_get_application_environment` right after the existing pops,
guarded by `getattr(sys, "frozen", False)`; on Linux
`restore_loader_library_path` runs first, then
`strip_frozen_qt_environment`. Removed entries are debug-logged. Runs
**before** the launch event is published, so any deliberate studio Qt
paths set via launch-config `environment_variables` or an integration
hook are applied afterwards and always win. Never touches `os.environ`,
so Connect's own UI is unaffected. Safe for the standalone helper: the
re-invoked frozen exe's own runtime hook re-creates these vars at
bootstrap.

Deliberately kept: `QT_PREFERRED_BINDING` (set intentionally for
children), `_PYI_*` (bootloader-managed, inert for non-PyInstaller
children), `QT_API`/`PYSIDE6_OPTION_PYTHON_ENUM` (set by qtpy via the
`qtawesome` import — indistinguishable from studio values, not paths,
not implicated here; see follow-ups).

### Layer 2 — Harmony hook (transitional)

`projects/framework-harmony/connect-plugin/hook/
discover_ftrack_framework_harmony.py`. A self-contained twin helper
(hooks must not depend on new Connect code):
`get_frozen_qt_environment_actions(environ=None, bundle_roots=None)`.
Defaults read `os.environ` and detect `sys.frozen`/bundle roots (same
multi-root logic as Layer 1, incl. the macOS app root); the parameters
exist for test injection. Returns Connect launch-env **actions** for the
four Qt path vars only:

- all entries under bundle roots → `"<VAR>.unset": "1"`
- mixed → `"<VAR>.set": "<foreign entries only>"`
- studio-only / absent / not frozen → no action.

Merged into `launch_data["integration"]["env"]` in
`on_launch_integration`. PATH/loader-path handling stays Layer-1-only to
keep the transitional surface minimal.

This protects users whose *already-installed* frozen Connect predates
Layer 1: the next framework-harmony plugin release reaches them before
the next Connect release does. Layer interplay is idempotent — on a
fixed Connect the hook's `.unset` no-ops and `.set` rewrites the
identical filtered value.

**Removal criteria:** remove the hook helper and its wiring once the
minimum supported Connect version ships the Layer 1 scrub (> 26.6.x).
The code carries a `TODO(remove)` block pointing here.

## Rejected: the standalone-side `setLibraryPaths` patch

A coworker's patch added `QApplication.setLibraryPaths()` inside
`ftrack_framework_harmony/__init__.py`. Rejected because it targets the
**wrong process**: the standalone helper is Connect's own frozen exe
re-invoked (`--run-framework-standalone`; frozen modules beat the
plugin's `dependencies/`), so its Qt and plugins always match — it
cannot emit these warnings. It also runs `setLibraryPaths()` *after*
`QApplication` creation, too late for the platform plugin. Redundant next
to the two layers.

## Other DCCs

Same latent leak (Houdini 21 = Qt 6.8 *silently* loads Connect's 6.6
plugins today; Qt5 DCCs warn). No DCC-specific fix exists or is needed —
Layer 1 covers them all once the next Connect ships.

## Tests

- `apps/connect/tests/unit/test_application_launcher_environment.py` —
  first tests in `apps/connect`; covers the frozen-path logic fully
  (helpers take roots as arguments, no frozen build needed). Added
  `[tool.pytest.ini_options] pythonpath = ["source"]` to
  `apps/connect/pyproject.toml`. A `connect-unit-pytest` CI job mirrors
  `harness-unit-pytest`.
- `projects/framework-harmony/tests/test_qt_env_scrub.py` — the primary
  verification vehicle. Unit cases (action emission + `on_launch`
  wiring), tier-1 live cases (fake frozen bundle composed exactly as
  Connect does → scrubbed env verified on the *live* Harmony process via
  `ps eww`, studio entry survives, JS package reconnects; a control
  launch proves the plumbing detects an unscrubbed leak) and a tier-2
  standalone case (captured standalone log free of
  `incompatible Qt library` lines). A small `apply_env_actions` helper in
  `tests/_launcher.py` mirrors Connect's `_get_integrations_environments`
  dispatcher so the tests apply hook actions the way Connect would.
  All groups pass against real Harmony 27 on the reference workstation.

## Follow-ups

- Snapshot `os.environ` before the `qtawesome` import
  (`ftrack_connect/__init__.py`) so `QT_API`/`PYSIDE6_OPTION_PYTHON_ENUM`
  studio values can be distinguished from qtpy-set ones.
- Paste the hook helper into maya/nuke/houdini/max hooks on their next
  releases (copy-paste siblings by repo convention; Adobe/Blender/Flame
  optional) until Layer 1 is the floor and Layer 2 is removed.
- Env scrub inside the future "clean interpreter" standalone runner
  (`apps/connect/.../__main__.py` TODO).
