# Harmony: make ftrack tools available at the launch screen

Status: deferred / future work
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

- The standalone helper now retries connecting **indefinitely** (was 2
  min), so if the artist sits at the launch screen and then opens a
  scene, ftrack still comes up. (`tcp_rpc.py`,
  `_connection_attempts = -1`; the process watchdog still terminates the
  helper when Harmony quits.)

## Proposed approach (deferred): launch straight into a scene

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
