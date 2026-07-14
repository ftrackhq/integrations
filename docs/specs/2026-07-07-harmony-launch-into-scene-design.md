# Harmony: make ftrack tools available at the launch screen

Status: implemented (approach A — launch into a bundled bootstrap scene)
Context: F-1087 (framework-harmony MVP), PR #656

## Problem

When Harmony launches without a scene it shows a minimal launch state,
not the full application. Investigation (Harmony 27 Premium, July 2026)
found two hard limits at that state:

1. Harmony shows a stripped **global "Stage Menu Bar"** (File / Edit /
   Help only). Script-registered menu items **cannot be added to it** —
   verified by registering at package-load time and by explicitly
   targeting `Stage Menu Bar/File`; nothing appears.
2. More fundamentally, **Harmony does not initialize package scripts
   until a scene UI loads**. Our ftrack package's `configure()` and its
   TCP server therefore never start at the launch screen — the whole
   integration is inert there. This is Harmony's architecture and is not
   influenceable from the package.

Consequence: at the launch screen the artist only gets `File > New` /
`Open…`, with no `ftrack Open`, even though opening a published scene
from ftrack is a likely first action.

## What already shipped in F-1087 (not this feature)

- The scene-switch survival mechanism was reworked: the TCP roles were
  **inverted** (standalone Python = server, Harmony JS = client that
  dials out), so the RPC channel outlives Harmony's engine teardown and
  the standalone no longer retries/reconnects. See
  `docs/specs/2026-07-14-harmony-menu-survives-scene-switch-design.md`.
  (This obsoletes the earlier "helper retries connecting indefinitely /
  `_connection_attempts = -1`" note.) The point below still holds: the
  ftrack package is inert at the no-scene launch screen regardless of
  transport, which is why launching straight into a scene is proposed.

## Implemented approach (A): launch straight into a scene

Never land on the launch screen. Connect launches Harmony with a bundled
blank bootstrap scene so the full UI (and thus the ftrack package +
`File > ftrack Open`) is live within ~10 s.

### What shipped

- **Bundled bootstrap scene** at
  `projects/framework-harmony/resource/bootstrap/scene/ftrack_bootstrap`.
  Created from a pristine `File > New` scene, then minimised empirically
  (each variant re-opened from a *staged* path to confirm a clean, prompt-
  free load) to 5 flat files (~24 KB): `ftrack_bootstrap.xstage`,
  `audio.tbl`, `scene.elementTable`, `scene.versionTable`, and a
  header-only `PALETTE_LIST`. Dropped as unnecessary: `.aux` (recovery),
  `files.vdb` (Harmony regenerates it on open), the default pencil-texture
  palette (1.1 MB, unreferenced by the `.xstage`), and all subdirectories
  (Harmony recreates the structure it needs). No absolute paths and no
  local-username metadata are committed (the `.xstage`/table `username`
  attributes are sanitised to `ftrack`).
- **Launch hook** (`connect-plugin/hook/discover_ftrack_framework_harmony.py`):
  `stage_bootstrap_scene()` copies the bundled folder into a fresh
  `tempfile.mkdtemp(prefix="ftrack_harmony_bootstrap_")` and returns the
  staged `.xstage`, which `on_launch_integration` appends to
  `integration["launch_arguments"]`. The temp root is exported as
  `FTRACK_HARMONY_BOOTSTRAP_SCENE` for cleanup.
- **Connect launcher** (`apps/connect/.../application_launcher/__init__.py`):
  after appending integration `launch_arguments`, on macOS it rewrites
  `["open", <app>.app, <file...>]` to `["open", "-n", "-a", <app>.app,
  <file...>]` — but only when a hook actually injected file arguments, so
  every other DCC's `open <app>` launch is unchanged. Windows/Linux receive
  the scene as a positional argument with no launcher change.
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
  staging so Harmony lands on the normal welcome/staging screen — today's
  behaviour. Could later surface as a Connect launcher preference/checkbox
  writing the same variable.

### Follow-up (approach B, deferred)

Present the ftrack Opener *before* launch and boot Harmony directly into the
chosen real scene (passed via the same `launch_arguments` path), skipping the
bootstrap-scene → real-scene switch. Reuses A's launcher plumbing; needs
reordering the launch orchestration (chooser → launch) and a "launch blank"
escape hatch that falls back to A.

### Original proposal (retained for context)

Never land on the launch screen. Have Connect launch Harmony with a
scene so the full UI (and thus the ftrack package + `File > ftrack
Open`) is live within ~10 s.

Verified building block: launching via
`open -n -a <Harmony.app> <scene.xstage>` boots Harmony **directly into
that scene**, the ftrack package initializes, and a custom environment
(`FTRACK_INTEGRATION_LISTEN_PORT` etc.) still propagates. The JS TCP
server was reachable ~10 s after launch (vs ~60 s via the normal
no-scene path).

Implementation sketch:

1. **Bundle a pristine blank "bootstrap" scene** in the plugin
   (`resource/`), or generate one on first launch.
2. **Connect launch hook** (`discover_ftrack_framework_harmony.py`,
   `on_launch_integration`): stage a per-launch copy of the bootstrap
   scene in a temp/user location (never hand the artist the shared
   original) and pass its `.xstage` to the launch command.
3. **macOS launch command**: Connect currently launches Harmony via
   `open <app>` (`apps/connect/.../application_launcher/__init__.py`
   ~line 1002). It needs to become `open -n -a <app> <scene.xstage>` (or
   the platform equivalent) — verify/extend how Connect passes file
   arguments through `open`, and the Windows/Linux equivalents.
4. The artist immediately uses `File > ftrack Open` to open their real
   scene from ftrack, which replaces the bootstrap scene.

## Risks / open questions

- Changing Connect's macOS launch command affects all DCCs launched via
  `open` — scope the change to Harmony (per-app launch command override).
- Windows/Linux launch-argument equivalents unverified.
- Bootstrap-scene lifecycle: staging per launch, cleanup, and making
  sure an unsaved bootstrap scene never blocks quit with a save prompt.
- Interaction with the trial-license flow on trial installs.

## Estimate

~half a day including testing, mostly in the Connect launch path and the
bootstrap-scene staging/cleanup.
