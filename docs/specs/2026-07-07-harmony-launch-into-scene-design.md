# Harmony: make ftrack tools available at the launch screen

Status: implemented (launch into a bundled bootstrap scene)

## Problem

When Harmony launches without a scene it shows a minimal launch state,
not the full application. Two hard limits apply at that state:

1. Harmony shows a stripped **global "Stage Menu Bar"** (File / Edit /
   Help only). Script-registered menu items **cannot be added to it** —
   neither by registering at package-load time nor by explicitly
   targeting `Stage Menu Bar/File`; nothing appears.
2. More fundamentally, **Harmony does not initialize package scripts
   until a scene UI loads**. The ftrack package's `configure()` and its
   TCP client therefore never start at the launch screen — the whole
   integration is inert there. This is Harmony's architecture and is not
   influenceable from the package.

Consequence: at the launch screen the artist only gets `File > New` /
`Open…`, with no `ftrack Open`, even though opening a published scene
from ftrack is a likely first action. The ftrack package is inert at the
no-scene launch screen regardless of transport, which is why launching
straight into a scene is the chosen approach. (For how the tools survive
subsequent scene switches once a scene is open, see
`docs/specs/2026-07-14-harmony-menu-survives-scene-switch-design.md`.)

## Design: launch straight into a scene

Never land on the launch screen. Connect launches Harmony with a bundled
blank bootstrap scene so the full UI (and thus the ftrack package +
`File > ftrack Open`) is live within ~10 s. The artist then uses
`File > ftrack Open` to open their real scene, which replaces the
bootstrap scene.

- **Bundled bootstrap scene** at
  `projects/framework-harmony/resource/bootstrap/scene/ftrack_bootstrap`.
  It is a minimised pristine `File > New` scene: 5 flat files (~24 KB) —
  `ftrack_bootstrap.xstage`, `audio.tbl`, `scene.elementTable`,
  `scene.versionTable`, and a header-only `PALETTE_LIST`. Harmony
  regenerates everything else on open (`files.vdb`, subdirectories, the
  default pencil-texture palette). No absolute paths and no local-username
  metadata are committed (the `.xstage`/table `username` attributes are
  `ftrack`).
- **Launch hook** (`connect-plugin/hook/discover_ftrack_framework_harmony.py`):
  `stage_bootstrap_scene()` copies the bundled folder into a fresh
  `tempfile.mkdtemp(prefix="ftrack_harmony_bootstrap_")` and returns the
  staged `.xstage`, which `on_launch_integration` appends to
  `integration["launch_arguments"]`. The temp root is exported as
  `FTRACK_HARMONY_BOOTSTRAP_SCENE` for cleanup.
- **Connect launcher** (`apps/connect/.../application_launcher/__init__.py`):
  after appending integration `launch_arguments`, on macOS it rewrites
  `["open", <app>.app, <file...>]` to `["open", "-n", "-a", <app>.app,
  "--args", <file...>]` — but only when a hook actually injected file
  arguments, so every other DCC's `open <app>` launch is unchanged.
  Windows/Linux receive the scene as a positional argument with no
  launcher change.
- **Cleanup** (`source/ftrack_framework_harmony/__init__.py`):
  `cleanup_bootstrap_scene()` removes the staged temp root, called from the
  process watchdog (`process_watchdog_callback`) just before
  `terminate_current_process()` when Harmony exits. Best-effort; the OS also
  reclaims the temp dir.
- **Toggle**: `FTRACK_HARMONY_LAUNCH_INTO_SCENE` (default on). Configured per
  variant in the launch config's `environment_variables` block
  (`extensions/launch/harmony-launch-{premium,advanced,essentials}.yaml`);
  `launch_into_scene_enabled()` reads it from the launch event
  (`application["environment_variables"]`) with the Connect process
  environment as a fallback. A falsy value (`0`/`false`/`no`/`off`) skips
  staging so Harmony lands on the normal welcome/staging screen. Could later
  surface as a Connect launcher preference/checkbox writing the same variable.

## Deferred alternative

Present the ftrack Opener *before* launch and boot Harmony directly into the
chosen real scene (passed via the same `launch_arguments` path), skipping the
bootstrap-scene → real-scene switch. This reuses the launcher plumbing above;
it needs reordering the launch orchestration (chooser → launch) and a "launch
blank" escape hatch that falls back to the bootstrap scene.

## Current constraints

- The Windows/Linux launch-argument path is untested; only macOS
  (`open -n -a <app> --args <scene>`) is validated.
- On trial installs the launcher dismisses the "Continue Trial" dialog
  and creates a temporary scene via accessibility automation, which needs
  the launching process to hold macOS **Accessibility** permission.
- The staged bootstrap scene is unsaved; cleanup relies on the process
  watchdog removing the temp root when Harmony exits.
