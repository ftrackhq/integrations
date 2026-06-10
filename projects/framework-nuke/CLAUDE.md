# framework-nuke — Claude guide

Notes for Claude (or any AI agent) working on the ftrack Framework Nuke integration. Complements `README.md` (which covers building/deploying) — this file covers architecture, conventions, and known rough edges that have tripped previous sessions.

## Layout

```
projects/framework-nuke/
├── source/ftrack_framework_nuke/        # importable package
│   ├── __init__.py                       # bootstrap_integration entry point
│   ├── asset/
│   │   ├── __init__.py                   # NukeFtrackObjectManager
│   │   ├── constants.py                  # re-exports base asset KEYS + Nuke-only constants
│   │   └── dcc_object.py                 # NukeDccObject (Backdrop tracking node)
│   └── utils/
│       └── __init__.py                   # nuke helpers + asset_link rename callback
├── extensions/                           # plugin discovery root (scanned at startup)
│   ├── nuke.yaml                         # dcc_config: menu tools and which tool-configs they run
│   ├── engines/
│   │   ├── nuke_asset_manager_engine.py  # NukeAssetManagerEngine.discover_assets et al
│   │   └── nuke_loader_engine.py
│   ├── plugins/                          # collectors, importers, validators, exporters, finalizers, AM plugins
│   ├── tool-configs/                     # YAML pipelines per tool
│   ├── widgets/
│   └── launch/                           # nuke-launch.yaml / nukex-launch.yaml for Connect
├── connect-plugin/__version__.py         # bumped per release
├── resource/bootstrap/menu.py            # Connect entry: imports ftrack_framework_nuke and registers menu
├── README.md                             # build + deploy steps
└── release_notes.md
```

The framework also pulls in shared code from `projects/framework-common-extensions/` (common dialogs, base loader/AM plugins, shared collector) and `libs/framework-core/` (engine, registry, plugin base). When tracking down behavior that doesn't live under `framework-nuke/`, check those two first.

## Architecture in one minute

Connect launches Nuke with `PYTHONPATH` and `FTRACK_FRAMEWORK_EXTENSIONS_PATH` set up to point at the deployed plugin folder. `resource/bootstrap/menu.py` imports `ftrack_framework_nuke`, which calls `bootstrap_integration(framework_extensions_path)` in `source/ftrack_framework_nuke/__init__.py`. That function:

1. Creates an `ftrack_api.Session` + `EventManager`.
2. Scans `extensions/` for plugins, engines, tool-configs, widgets, dialogs, launch-configs, dcc_configs via `ftrack_framework_core.registry`.
3. Spins up a `Host` and `Client` from `framework-core`.
4. Reads the `framework-nuke` dcc_config (`extensions/nuke.yaml`) and adds each tool's command to the Nuke "ftrack" menu, wired to `on_run_tool_callback(name, dialog_name, options)`.
5. Registers `addKnobChanged` callbacks for `asset_link` rename tracking (see below).

When the user clicks a menu item, the Client looks up the named tool config (e.g. `nuke-render-loader`) and runs its `engine` chain — each step is a plugin lookup against the registry.

### Tools currently wired

- `framework_standard_publisher_dialog` → `nuke-script-publisher`
- `framework_standard_opener_dialog` → `nuke-script-opener`
- `framework_asset_manager_dialog` → `nuke-asset-manager`
- `framework_loader_dialog` → `nuke-render-loader` (and `nuke-geometry-loader` when wired)
- `nuke-setup-scene` runs on Nuke startup (no UI).

## Loader pipeline (the v3–v5 hot path)

Tool configs declare a chain of `type: plugin` and `type: group` entries under `engine:`. For the loader, the chain is:

1. `common.loader_asset_picker` — context plugin that drives the dialog's AssetVersion picker.
2. Per-filetype `group` blocks, each containing:
   - `common.context_loader_collector` — queries ftrack, resolves component path, **populates `store['context_data']`, `store['component_data']`, `store['result']`** so the importer has everything it needs.
   - `nuke.native_loader_importer` (or `nuke.abc_loader_importer`) — runs `init_and_load` from `framework_common_extensions/source/ftrack_framework_loader/plugins/base_loader_importer.py`:
     - `init_nodes`: build `FtrackAssetInfo`, create a Backdrop via `NukeDccObject`, sync knobs.
     - `run_custom`: create the actual Read / ReadGeo2 / AudioRead / Camera2 node and set `file`.
     - `load_asset`: snapshot diff of `nuke.allNodes()` names before/after `run_custom`, then `connect_objects(diff)` to wrap the Backdrop around the new node(s).
   - `common.passthrough_loader_post_importer` — no-op stub.
3. `common.passthrough_loader_finalizer` — no-op stub.

The base `init_and_load` **merges** init_result into `store['result']` (rather than overwriting) so the collector's `component_path` survives for `run_custom`. This is a recent fix — preserve it.

## DCC tracking design

Each loaded component produces **one Backdrop** wrapping **one content node**.

- The Backdrop is the ftrack "tracking node" — it carries the `ftracktab` Tab_Knob and a String_Knob per entry in `ftrack_framework_asset_manager.asset.constants.KEYS` (asset_info_id, version_id, component_name, component_path, …). All 16 base keys must exist as knobs; missing keys make `FtrackObjectManager._sync` crash silently. `ftrack_framework_nuke.asset.constants.KEYS` is `list(asset_const.KEYS)` to keep this aligned.
- The Read sits inside the Backdrop **geometrically** — `connect_objects` computes a bounding box around the just-created Read and resizes the Backdrop to wrap it. `backdrop.getNodes()` then returns the contained Reads on read.
- The `asset_link` knob holds the wrapped Read's name as a static `;`-joined string. **See "Known rough edges" → asset_link.**

Reading a tracked asset back: scan `nuke.allNodes(recurseGroups=True)` for nodes with the `ftracktab` knob (`utils.get_nodes_with_ftrack_tab`), then `NukeDccObject.dictionary_from_object(name)` reads each knob whose name is in `asset_const.KEYS` and reconstructs an `FtrackAssetInfo`.

## Asset Manager

The AM dialog is plugin-driven, not engine-method-driven. `AssetManagerDialog._on_rebuild()` calls `run_tool_config(reference)`; the dialog's `plugin_run_callback` fires after every successful plugin step and refreshes the list whenever `store['versions']` is set (last writer wins).

`nuke-asset-manager.yaml` chains:

1. `am_test_discover` — sets `store['discover_filter']` (no scene scan).
2. `am_update_latest_action` — ftrack-side version lookup; logs a benign "Missing required data" warning when invoked without an asset_info.
3. `am_default_resolver` — task-linked AssetVersion resolution from ftrack (often `[]` for these task contexts).
4. `nuke.am_scene_discover` — **the scene-side walker**. Iterates `get_nodes_with_ftrack_tab()`, rebuilds an `FtrackAssetInfo` per Backdrop, writes the list to `store['versions']`. Runs last so it wins.

`NukeAssetManagerEngine.discover_assets()` still exists with the same scan logic and is reachable from `select_assets` / `remove_assets` paths via `DccObject(from_id=…)` lookups — keep both in sync if you change the scan.

## Build + deploy

```bash
cd projects/framework-nuke
uv build
uv run python ../../tools/build.py --include_resources resource/bootstrap build_connect_plugin .
rm -rf ~/Documents/ftrack_connect_plugins/ftrack-framework-nuke-<version>
cp -R dist/ftrack-framework-nuke-<version> ~/Documents/ftrack_connect_plugins/
```

`uv build` produces the wheel/sdist; `build_connect_plugin` bundles a deployable directory + zip under `dist/`. Nuke launched from Connect picks up the deployed folder via launch yamls. **Restart Nuke after redeploying** — Python module imports are cached.

## Logs

- Connect launcher: `~/Library/Application Support/ftrack-connect/log/ftrack_connect.log`
- Nuke framework runtime: `~/Library/Application Support/ftrack-connect/log/ftrack_framework_nuke.log` — this is where loader/AM plugin tracebacks land. Always check this first when something looks broken in Nuke.

## Known rough edges (TODOs / stopgaps)

### `asset_link` is a static string with a rename callback

**Where:** `source/ftrack_framework_nuke/asset/dcc_object.py:connect_objects` and `source/ftrack_framework_nuke/utils/__init__.py:sync_asset_link_on_rename`.

**What's happening:** the `asset_link` knob on the Backdrop is a plain `String_Knob` that holds the wrapped content node's name as text. Renames are kept current by an `addKnobChanged` callback registered at bootstrap for `Read` / `ReadGeo2` / `AudioRead` / `Camera2` — on a `name` change, the callback walks every ftrack-tagged Backdrop, checks `backdrop.getNodes()`, and rewrites `asset_link` to match.

**Why not a Link_Knob:** the intent was `nuke.Link_Knob.setLink('<read>.name')` so Nuke's expression engine would handle the rename rewrite natively. Two Nuke quirks defeated that:

1. Link_Knobs are created with `INVISIBLE = 1024` by default. `clearFlag(nuke.INVISIBLE)` alone didn't make ours render.
2. Knobs added programmatically after node creation tend to land in a "User" tab rather than the tab they were added under (per Shotgun's `tk-nuke-writenode/handler.py:1162-1172` comment).

We tried the Shotgun pattern (`knobs()[name]` dict access + `setLink` → `setLabel` → `clearFlag(INVISIBLE)`), `EvalString_Knob.setValue('[value <read>.name]')`, and `String_Knob.setExpression('<read>.name')`. None rendered. Revisit if a workable Link_Knob recipe emerges — likely involves pre-allocating link knobs in a Group-style node template rather than `addKnob`-ing at runtime.

### AM widget field-name mismatches

`AssetManagerWidget.set_asset_info` (in `framework-common-extensions/source/ftrack_framework_asset_manager/ui/asset_manager_widget.py`) reads `asset_info.get("version_nr")`, `.get("path")`, `.get("versions")` — but `FtrackAssetInfo` exposes `version_number`, `component_path`, and no `versions` list. Rows show up after scene discovery but some labels render blank/wrong. Out of scope for the recent loader fixes; separate ticket.

### `_set_scene_node_color(ftrack_node)` arg misuse

`NukeDccObject.create()` calls `self._set_scene_node_color(ftrack_node)`, but the method's signature is `_set_scene_node_color(self, latest=True)`. A Nuke `Node` is truthy, so the call accidentally behaves like `latest=True`. Not blocking anything; clean up if you're already in the file.

## Conventions

- **Knob naming for ftrack-tagged Backdrops** comes from `ftrack_framework_asset_manager.asset.constants.KEYS`. Don't hand-roll knob names; reference the constants.
- **`@nuke_utils.run_in_main_thread`** wraps any function that touches the Nuke API from a background thread. The engine fires plugins on worker threads.
- **Main thread reentrancy**: stacking `@run_in_main_thread` on a function already called from the main thread is safe — the decorator short-circuits.
- **Build/copy from `projects/framework-nuke`**: `uv build` and the Connect-plugin build step assume that working directory.
- **`set_tool_config_option(options, item_reference)`** at the dialog level: pass `item_reference=None` to write top-level (engine sees it on every plugin); pass the plugin's reference to scope to one plugin. Used by the loader dialog's `Load Mode` dropdown.

## When making changes

- Edit, build, deploy, **restart Nuke** (Connect-launched Nukes hot-load Python from the deployed bundle once and cache).
- Test path: open the Loader on a known-good task, LOAD a row, check the `ftrack_framework_nuke.log` for `ERROR` / `Traceback`, then open the Asset Manager and confirm the row appears.
- The repo's tool-configs ship as YAML in `extensions/tool-configs/`. The deployed bundle has copies under `dist/.../extensions/nuke/tool-configs/`. If a YAML edit doesn't seem to take effect, rebuild — the deployed copy is what Connect reads.
