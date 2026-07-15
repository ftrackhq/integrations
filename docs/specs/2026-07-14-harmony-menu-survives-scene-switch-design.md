# Harmony: ftrack menu that survives scene switches — invert the TCP roles

Status: implemented

## Problem

Harmony has no embedded Python, so the ftrack menu/toolbar/shortcut is
built from QtScript. Harmony tears down its **QScriptEngine** (the JS
context) on **every** scene open/create/close, and does **not**
re-invoke a package's `configure()`. Only the `TB_sceneOpened` /
`TB_sceneCreated` hooks reliably run on a scene switch.

A TCP **server** living inside Harmony's JS dies with the engine on
every scene switch, so it structurally cannot survive them: the menu
items can be re-registered by the scene hooks, but they go **dead on
click** because their RPC channel is gone, and the toolbar vanishes.
Rebuilding an in-engine server from the hooks and having the standalone
reconnect forever is fragile — the reconnect loop also blocks the Qt
event loop and breaks clean shutdown. The transport must therefore keep
the server outside the engine.

## Chosen approach: invert the TCP roles

Both mature open-source Harmony integrations — AYON/OpenPype
(`ynput/ayon-harmony`) and ShotGrid `tk-harmony` — put the **TCP server
in the external Python process** and make **Harmony the client that
dials out**. An external server outlives every scene switch, so the RPC
channel never dies with the engine. This structurally eliminates the
problem rather than patching it.

- **Standalone Python process = TCP *server*** (`utils/tcp_rpc.py`,
  class name `TCPRPCClient` kept — it is the role-agnostic RPC channel;
  callers still do `TCPRPCClient.instance().rpc(...)`). Binds
  **`127.0.0.1` only** (loopback bind avoids the macOS firewall prompt;
  never bind `0.0.0.0`/`Any`) and listens for Harmony's whole lifetime.
- **Harmony JS = TCP *client*** (`configure.js`, class `TCPClient`).
  Socket parented to `QCoreApplication.instance()` (not the transient
  engine). Dials out from `configure()` at launch and from the scene
  hooks after every switch.

**Rejected sub-detail from AYON:** hanging the menu on the persistent
`QMainWindow.menuBar()` fails on macOS (native NSMenu, zero-height, no
runtime repaint). We keep registering menu items via
`ScriptManager.addMenuItem` into the existing **File** menu, and the
toolbar + shortcut remain the primary grouped ftrack surface.

### Wire framing is unchanged by the flip

The Qt framed wire protocol is asymmetric **by direction, not by role**:

- **Python → Harmony**: big-endian `uint32(len+1)` + UTF-8 JSON +
  trailing NUL (`QDataStream.writeString`; JS strips the NUL).
- **Harmony → Python**: big-endian `int32(len)` + raw UTF-8 JSON.

Python keeps *sending* CONTEXT_DATA/RPC and *receiving* replies, so both
send and receive bodies are direction-symmetric with the previous
transport; only the socket lifecycle differs (listen/accept instead of
connect).

## Handshake

```
Connect launch hook: picks free PORT -> FTRACK_INTEGRATION_LISTEN_PORT; deploys JS;
launches Harmony AND spawns the standalone.

STANDALONE (Python, long-lived)          HARMONY (JS, transient per-scene engine)
  bootstrap_integration()
    server.listen(127.0.0.1, PORT)  <---- binds immediately (no sleep)
    start PID watchdog; app.exec()
        |                                 scene open/create -> TB_scene* hook runs
        |                                 -> re-include configure.js
        |                                 -> ftrackRebuildMenus()  (menu back NOW)
        |                                 -> ftrackConnectIntegration()
   newConnection <===== connectToHost(127.0.0.1, PORT)  [QTcpSocket parented to app]
   accept; abort any stale prev socket; reset framing; wire signals
   send(CONTEXT_DATA {context_id,launchers}) ===> rebuild menu(File) + toolbar/shortcut once
   reply <=== (menu rebuilt; items now functional)
   first accept only -> on_connected_callback() (startup tools ONCE, via _ever_connected)
   ...Python-initiated rpc() (getScenePath/renderSequence) over same socket...
   --- SCENE SWITCH: old socket dies; server KEEPS LISTENING; new engine dials again ---
   --- HARMONY QUITS: PID watchdog (5s) -> terminate_current_process() ---
```

## Menu restoration is belt-and-suspenders (both parts required)

A pure "single source of truth via CONTEXT_DATA on reconnect" design is
insufficient: the menu would depend on an async round trip
(dial → accept → CONTEXT_DATA → rebuild) initiated from a transient
scene-hook engine, so any hiccup leaves the menu gone. The design keeps
a synchronous re-registration alongside it:

1. **`TB_scene*` hooks** re-include `configure.js`, then call
   **`ftrackRebuildMenus()` synchronously** — the menu is back
   immediately from the persisted `ftrack_launchers_json` string (File
   menu, stable ids `ftrackMenu<name>ID` so re-adds replace, not
   duplicate), independent of the network.
2. Then **`ftrackConnectIntegration()`** re-dials the still-listening
   server; on connect the server re-sends CONTEXT_DATA which rebuilds
   the menu again (idempotent) **and makes the items functional** (the
   RPC channel is live).
3. **Toolbar + shortcut** are rebuilt on each (re)connection too — they
   do **not** survive a scene switch either. They are guarded by an
   **instance** flag `this.ftrack_ui_built` on the `HarmonyIntegration`
   (recreated per reconnect), so they rebuild once per scene switch while
   a second CONTEXT_DATA on the same connection can't stack a duplicate.
   Stable ids (`ftrackToolbar`/`ftrackShortcut`) keep the re-add
   idempotent.

## Invariants (load-bearing — do not regress)

- **`ftrackConnectIntegration()` must never early-return on connection
  state.** It always creates a fresh `HarmonyIntegration` and dials. A
  guard like `if (app.integration.tcp_client.connected) return;` breaks
  every reconnect after the first: the new engine reads the *dead
  old-engine copy* of `connected` as stale-**true**, returns early, never
  re-dials, and the menu stays dead after the first scene switch.
  Re-connecting is safe — the server aborts the stale socket when the new
  one connects (`_on_new_connection`), and menu/toolbar re-registration
  is idempotent.
- **The UI-rebuild guard must live on the per-connection
  `HarmonyIntegration` instance, never the persistent application
  object.** The toolbar and shortcut are torn down with the menu items on
  every scene switch, so their guard must reset per switch. A flag on the
  persistent `QCoreApplication` outlives scene switches, sticks `true`
  after the first build, and makes the toolbar vanish after the first
  switch. `this.ftrack_ui_built` on the per-reconnect instance is `false`
  again after each switch, so the toolbar and shortcut rebuild alongside
  the menu while a second CONTEXT_DATA on one connection still can't
  stack a duplicate.

## Implementation map

- **`utils/tcp_rpc.py`** — server role: `listen()` binds `127.0.0.1`;
  `_on_new_connection` drains `nextPendingConnection`, aborts any stale
  prior socket, wires per-connection signals, sends CONTEXT_DATA, and
  runs startup tools on the first accept only (`_ever_connected`). The
  send/receive framing targets the current `_connection`. On disconnect
  it resets and keeps listening (no reconnect loop, no terminate); the
  synchronous `send()` spin fails fast if the connection drops mid-wait.
- **`__init__.py`** — binds the server (`listen(on_listen_failure_callback)`)
  at bootstrap and relies on the PID watchdog as the **only** shutdown
  trigger. `setQuitOnLastWindowClosed(False)`.
- **`configure.js`** — `TCPClient` dials out with its socket parented to
  the app. `handleIntegrationContextDataCallback` rebuilds the menu on
  every CONTEXT_DATA and rebuilds toolbar+shortcut once per connection,
  guarded by the instance flag `this.ftrack_ui_built`.
  `ftrackConnectIntegration()` always dials afresh (no guard).
- **`TB_sceneOpened.js` / `TB_sceneCreated.js`** — each hook chains the
  default, then re-includes `configure.js` → `ftrackRebuildMenus()`
  (sync) → `ftrackConnectIntegration()` (reconnect).
- **`discover_ftrack_framework_harmony.py`** — picks a free port
  (`FTRACK_INTEGRATION_LISTEN_PORT`, the port Python *binds* and Harmony
  dials), sets `FTRACK_HARMONY_PACKAGE_PATH`, deploys the JS, and cleans
  up stale `[ftrack]`-marked hooks.
- **Tests** (`tests/`) — the test process is the **server** Harmony
  dials: `_rpc_client.py` listens/accepts (framing/handshake/rpc reused);
  `conftest.py` creates the scene in the consuming fixtures so the server
  listens **before** Harmony dials (tier-1 `harmony_connection`; tier-2
  `standalone_bundle`).

## Risks / gotchas

- **Deployed JS only refreshes on launch.** `sync_js_plugin` copies the
  bootstrap JS into Harmony's scripts folder
  (`<prefs>/Toon Boom Animation/Toon Boom Harmony <variant>/<version>00-scripts/packages/ftrack/`)
  at launch; a running Harmony keeps its old JS. Different installed
  versions (25 vs 27) go stale independently — relaunch the version you
  test.
- **macOS firewall** — mitigated by binding `127.0.0.1` only.
- **Port in use on relaunch** — Connect picks a fresh random free port
  per launch; `listen()` failure → `sys.exit(-1)` with a clear log.
- **In-flight RPC during a scene switch** loses its reply — handled by
  the fail-fast guard in `send()`.
- If the hooks are ever stripped again, `sync_js_plugin` must also DELETE
  previously-deployed `[ftrack]` TB_scene hooks, or a stale hook keeps
  firing and breaks scene creation.

## Verifying (Harmony 27 / 25, macOS)

Deploy per the build+deploy rule (`uv build` **without** `--from_source`,
**with** `--include_resources resource/bootstrap`; deploy the Connect
plugin; restart Connect with `FTRACK_CONNECT_PLUGIN_PATH`; relaunch
Harmony so the new JS is deployed). Then repeatedly exercise File > New /
File > Open and confirm:

- the ftrack menu, toolbar and shortcut all stay present and clickable
  after every scene switch (not just the first);
- the toolbar is neither dropped nor duplicated;
- the standalone log
  (`~/Library/Application Support/ftrack-connect/log/ftrack_framework_harmony.log`)
  shows a fresh `Successfully established connection` + CONTEXT_DATA after
  **every** scene switch, with startup tools running exactly once.
