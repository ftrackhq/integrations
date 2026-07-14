# Harmony: ftrack menu that survives scene switches — invert the TCP roles

Status: implemented (F-1087, framework-harmony MVP)
Context: supersedes the transport design in the earlier scene-hook /
"re-register the menu once" attempts.

## Problem

Harmony has no embedded Python, so the ftrack menu/toolbar/shortcut is
built from QtScript. Harmony tears down its **QScriptEngine** (the JS
context) on **every** scene open/create/close, and does **not**
re-invoke a package's `configure()`. Only the `TB_sceneOpened` /
`TB_sceneCreated` hooks reliably run on a scene switch.

The original transport put the **TCP server inside Harmony's JS** and
made the **standalone Python process the client**. Because the JS server
died with the engine on every scene switch, the menu items reappeared
(the scene hooks re-registered them) but went **dead on click**, and the
toolbar vanished. Attempts to rebuild the in-engine server from the
hooks + make the standalone reconnect forever were fragile (the
reconnect loop also broke clean shutdown by blocking the Qt event loop).

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
`_send`/`send` and `_receive`/`handleEvent` bodies were reused verbatim.
Only the socket lifecycle moved (listen/accept instead of connect).

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

A pure "single source of truth via CONTEXT_DATA on reconnect" design was
tried first and **failed**: the menu depends on an async round trip
(dial → accept → CONTEXT_DATA → rebuild) initiated from a transient
scene-hook engine, so any hiccup leaves the menu gone. The robust design
keeps the proven synchronous re-registration:

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
   idempotent. (See "The toolbar-persistence bug" below — the guard was
   originally on the persistent application object, which stuck `true`
   across scene switches and blocked every rebuild.)

## The idempotency-guard bug (found during verification)

The first cut of the flip added an idempotency early-return to
`ftrackConnectIntegration()`:
`if (app.integration.tcp_client.connected) return;`. **This blocked
every reconnect after the first** and is the reason "the menu still
disappears after a scene change." Traced via the standalone log
(`~/Library/Application Support/ftrack-connect/log/ftrack_framework_harmony.log`):

- First scene: `app.integration` is undefined → guard falls through →
  connects fine, menu built.
- Every subsequent switch: the new engine reads
  `app.integration.tcp_client.connected` back from the **dead old-engine
  copy** as stale-**true** → returns early → never re-dials → the
  standalone logs "DCC connection dropped ... awaiting reconnect" and
  then nothing.

**Fix:** delete the guard. `ftrackConnectIntegration()` always creates a
fresh `HarmonyIntegration` and dials. Re-connecting is safe: the server
aborts the stale socket when the new one connects
(`_on_new_connection`), and the menu/toolbar re-registration is
idempotent.

## The toolbar-persistence bug (found after the flip)

Same shape as the guard bug above, on a different object. The toolbar
and shortcut were built once behind `app.ftrack_ui_built` — a flag on
the persistent `QCoreApplication`, chosen on the (wrong) assumption that
"the toolbar and shortcut persist across scene switches." They do not:
Harmony tears them down with the menu items on every scene switch. But
the flag lives on the app object, which *does* outlive scene switches,
so after the first build it stayed `true` and every later scene switch
skipped the rebuild — the toolbar vanished after the first switch while
the (unguarded) menu items kept coming back.

**Fix:** move the guard from the persistent application to the
per-connection `HarmonyIntegration` instance (`this.ftrack_ui_built`),
which is recreated on every reconnect. The flag is therefore `false`
again after each scene switch, so the toolbar and shortcut are rebuilt
alongside the menu, while a second CONTEXT_DATA on one connection still
can't stack a duplicate.

## Changes by file

- **`utils/tcp_rpc.py`** — server role. New `listen(on_listen_failure)`
  (binds `127.0.0.1`), `_on_new_connection` (drain
  `nextPendingConnection`, abort stale prev socket, wire per-connection
  signals, send CONTEXT_DATA, first-accept-only startup tools). `_send`/
  `_receive` retargeted `self.socket` → `self._connection` (framing
  unchanged). `_on_disconnected` gutted to reset-only (server keeps
  listening; no reconnect loop, no terminate). `send()` synchronous spin
  gained a fail-fast guard if the connection drops mid-wait. Deleted:
  `connect_dcc`, `_connect_to_host`, `_check_connection`, `_on_connected`,
  indefinite retry, `_signals_connected`, the connect `QTimer`.
- **`__init__.py`** — dropped `time.sleep(2)`; `connect_dcc(...)` →
  `listen(on_listen_failure_callback)`. Watchdog unchanged and now the
  **only** shutdown trigger. `setQuitOnLastWindowClosed(False)` kept.
- **`configure.js`** — `TCPServer` → `TCPClient` (dials out, socket
  parented to the app). `handleIntegrationContextDataCallback` rebuilds
  the menu on every CONTEXT_DATA and rebuilds toolbar+shortcut once per
  connection, guarded by the instance flag `this.ftrack_ui_built`.
  `ftrackEnsureIntegration` → `ftrackConnectIntegration`
  (no guard, no close-previous-server block). `shutdown` →
  `tcp_client.socket.abort()`, `aboutToQuit` best-effort only.
- **`TB_sceneOpened.js` / `TB_sceneCreated.js`** — each hook chains the
  default, then `ftrackReconnectHook()`: re-include `configure.js` →
  `ftrackRebuildMenus()` (sync) → `ftrackConnectIntegration()` (reconnect).
- **`discover_ftrack_framework_harmony.py`** — unchanged behaviour
  (free-port pick → `FTRACK_INTEGRATION_LISTEN_PORT`, now the port Python
  *binds* and Harmony dials; `FTRACK_HARMONY_PACKAGE_PATH`; stale-hook
  cleanup + `[ftrack]` marker preserved).
- **Tests** (`tests/`) — harness role inverted: the test process is now
  the **server** Harmony dials. `_rpc_client.py` `connect_with_retry` →
  `listen()`+`accept()` (framing/handshake/rpc reused). `conftest.py`
  moves scene creation out of `harmony_process` into the consuming
  fixtures, so the server is listening **before** Harmony dials (tier-1
  `harmony_connection`; tier-2 `standalone_bundle`).

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

## Verification (Harmony 27 / 25, macOS)

Deploy per the build+deploy rule (`uv build` **without** `--from_source`,
**with** `--include_resources resource/bootstrap`; deploy the Connect
plugin; restart Connect with `FTRACK_CONNECT_PLUGIN_PATH`; relaunch
Harmony so the new JS is deployed). Confirmed working across repeated
File > New / File > Open: the ftrack menu, toolbar and shortcut all stay
present and clickable, the toolbar is neither dropped nor duplicated,
and the standalone log shows a fresh
`Successfully established connection` + CONTEXT_DATA after **every**
scene switch (not just the first), with startup tools running exactly
once.
