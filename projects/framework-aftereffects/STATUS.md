# After Effects UXP Integration — Status

## Current State (2026-04-22)

The ftrack After Effects UXP integration is **code-complete** but **cannot be installed** into After Effects due to missing third-party UXP plugin infrastructure on Adobe's side.

The Python package (`uv sync`, `uv build`), the Connect plugin build (`build_connect_plugin`), and the UXP artifact build (`build_uxp` → `.ccx`) all succeed without issues.

## The Problem

After Effects ships with a UXP runtime but does **not** support loading third-party UXP panel plugins. Two separate gaps exist:

### 1. Missing `uxphostcode` in Adobe's UPI Database

The UCF installer (`UnifiedPluginInstallerAgent`) uses a SQLite database at:
```
/Library/Application Support/Adobe/UPI/Configuration/DB/UPISys.db
```

The `Tb_XManConfig` table maps manifest `host.app` values to products via a `uxphostcode` field:

| ProdID | Product | `uxphostcode` | `uxphybridsupport` |
|--------|---------|---------------|---------------------|
| 318 | Photoshop | `PS` | `true` |
| 315 | Premiere Pro | `premierepro` | `true` |
| 313 | After Effects | **(missing)** | **(missing)** |

Without this mapping, `UnifiedPluginInstallerAgent --install` fails with status **-411** (unknown host app) for object-format manifests and **-267** for array-format manifests.

**Workaround tested:** Patching the database manually makes UCF installation succeed:
```bash
sudo sqlite3 "/Library/Application Support/Adobe/UPI/Configuration/DB/UPISys.db" \
  "INSERT OR REPLACE INTO Tb_XManConfig VALUES(313, 'uxphostcode', 'aftereffects');" \
  "INSERT OR REPLACE INTO Tb_XManConfig VALUES(313, 'uxphybridsupport', 'true');" \
  "INSERT OR REPLACE INTO Tb_XManConfig VALUES(313, 'minupiversion', '8.1');"
```

After patching, UCF installs the CCX to `~/Library/Application Support/Adobe/UXP/Plugins/External/` and registers it in the user UPI database correctly (ProdID 313, Enabled). **However, this alone does not make AE load the plugin** — see gap #2.

### 2. Missing `upic` Plugin Loader in After Effects' UXP Runtime

Photoshop's UXP runtime includes a `upic` (UXP Plugin Installer Client) subsystem that discovers and loads third-party plugins from `Plugins/External/`. This is visible in Photoshop's UXP log:

```
upic::Loading plugins from user PluginsInfo file
upic::plugin with id: com.ftrack.framework.photoshop.uxp.panel is added in uxp plugin manager with status as enabled
```

**After Effects' UXP runtime has no `upic` messages at all.** It does not scan `Plugins/External/` and does not load third-party plugins. This was confirmed on both:

- After Effects 2026 stable (v26.2, build 49)
- After Effects 2026 Beta (v26.3, build 51)

## What Was Tested

### Installation Methods

| Method | Result |
|--------|--------|
| `UnifiedPluginInstallerAgent --install` (without DB patch) | **-411** (unknown host) |
| `UnifiedPluginInstallerAgent --install` (with DB patch, object host) | **Success** — but AE doesn't load it |
| `UnifiedPluginInstallerAgent --install` (array host format) | **-267** (even with DB patch) |
| Manual extract to `~/...UXP/Plugins/External/` | AE never scans this directory |
| Manual copy to `/Library/.../UXP/extensions/` (system dir) | AE parses manifest, no errors, but **does not execute JS or create menu entry** |
| Copy to AE app bundle `Contents/UXP/plugins/` | **Blocked by SIP** (`Operation not permitted`) |
| UXP Developer Tool sideload | Not viable — AE must be launched via ftrack Connect |

### Manifest Formats

| Format | UCF Install (with DB patch) | AE Runtime |
|--------|---------------------------|------------|
| Object: `"host": {"app": "aftereffects", ...}` | Success | Parsed, not loaded |
| Array: `"host": [{"app": "aftereffects", ...}]` | -267 | Parsed, not loaded |

### Key Log Evidence

After Effects UXP log when plugin is in the system extensions directory:
```
Plugin com.ftrack.framework.aftereffects.uxp.panel : Scaled Icon : icons/ftrack-logo-48@1x.png not found
Plugin com.ftrack.framework.aftereffects.uxp.panel : Scaled Icon : icons/ftrack-logo-48@2x.png not found
```
No errors, but no JS execution follows. Compare with Photoshop where `[ftrack panel] Initialising integration.` appears immediately after manifest parsing.

AE confirms `"aftereffects"` is the correct `host.app` value:
```
Plugin com.adobe.substance-3d.viewer.ps : Expected 'host.app' to be aftereffects
```

AE Beta (v26.3) bundles working UXP panels internally at `Contents/UXP/plugins/`:
- `com.adobe.dva.ae.findandreplace` — "Find and Replace Text" panel
- `com.adobe.stock.unified.content.panel` — Adobe Stock panel

These use array-format host with AE-specific dependencies (`dvascripting`, `dvauxpui`).

## Correct Manifest `host.app` Value

The correct identifier for After Effects in UXP manifests is **`"aftereffects"`** (lowercase, one word). This is confirmed by:
- AE's own UXP log error message: `Expected 'host.app' to be aftereffects`
- AE's HostData: `"Product": "aftereffects"`
- Adobe's bundled Stock panel manifest targeting AE

## File Locations Reference

| Path | Purpose |
|------|---------|
| `/Library/Application Support/Adobe/UPI/Configuration/DB/UPISys.db` | System UPI database (product→uxphostcode mapping) |
| `~/Library/Application Support/Adobe/UPI/Configuration/DB/UPI.db` | User UPI database (installed extensions) |
| `~/Library/Application Support/Adobe/UXP/Plugins/External/` | UCF-installed third-party plugins |
| `/Library/Application Support/Adobe/UXP/extensions/` | System-level UXP extensions (scanned by all Adobe apps) |
| `~/Library/Application Support/Adobe/UXP/PluginsInfo/v1/` | Per-host plugin info files |
| `~/Library/Logs/Adobe/Adobe After Effects 2026/` | AE stable UXP logs |
| `~/Library/Logs/Adobe/Adobe After Effects (Beta)/` | AE Beta UXP logs |
| App bundle `Contents/UXP/plugins/` | Internal bundled UXP plugins (SIP protected) |

## UCF Installer Location

```
/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app/Contents/MacOS/UnifiedPluginInstallerAgent
```

Usage:
```bash
# Install
"<path-to-agent>" --install "<path-to-ccx>"

# Remove
"<path-to-agent>" --remove "<extension-name>"
```

## Build Commands

From `projects/framework-aftereffects/`:

```bash
# Build the UXP CCX artifact
uv run --python 3.13 python ../../tools/build.py --remove_intermediate_folder build_uxp .

# Build the Connect plugin (includes CCX as asset)
uv build && \
uv run --python 3.13 python ../../tools/build.py --remove_intermediate_folder \
  --include_assets "$(find "$PWD/dist" -type f -name '*.ccx')" \
  build_connect_plugin .
```

## Next Steps

1. **Wait for Adobe** to add `upic` support to After Effects' UXP runtime and `uxphostcode` to the UPI database. This is the only sustainable path.
2. **SIP bypass** (disable SIP, copy to app bundle, re-enable) could work for development testing but is not viable for distribution.
3. **File a request with Adobe** referencing the missing `upic` subsystem and `uxphostcode` for After Effects in the UPI/UCF tooling.
4. **Monitor AE Beta releases** — the Beta (v26.3) bundles UXP panels (`findandreplace`, `stock`), suggesting Adobe is actively developing this. Third-party support may follow.
