# UV Migration Context (Handoff)

This file captures the current migration state so a new agent can resume work in a fresh context.

## Branch / Push Status

- Branch: `fi-7_use-uv-and-ruff-for-main-repo-management`
- Latest pushed commit: `30e076fb4`
- Push completed to remote.

## What Has Been Migrated

### Root + CI + Tooling

- Root moved to Python `>=3.13,<3.14` and uv lock regenerated.
- CI workflows migrated to uv:
  - `.github/workflows/build-library.yml`
  - `.github/workflows/build-connect.yml`
  - `.github/workflows/build-plugin.yml`
  - `.github/workflows/push-main-test.yml`
- `tools/build.py` updated for uv-first usage and Python 3.13 compatibility.
  - `distutils.spawn` replacement via `shutil.which`
  - CEP `--nosign` path fixed (no forced ZXPSignCmd/cert checks)
  - Framework DCC detection fixed for PEP621 projects
  - uv export/install flow for plugin dependency packaging
  - RV rvpkg artifact naming uses major.minor (e.g. `26.3`)

### Libraries (`libs/*`)

- All target libs migrated to uv/PEP621/Hatch and bumped to major `4.0.0`:
  - `ftrack-constants`
  - `ftrack-utils`
  - `ftrack-framework-core`
  - `ftrack-framework-qt`
  - `ftrack-qt`
  - `ftrack-qt-style`
- `ftrack-python-api` direct requirements moved to `>=3.1.0,<4.0.0` where applicable.
- Local `uv.lock` created for each migrated lib.

### Connect (`apps/connect`)

- Connect aligned to uv and updated to consume libs 4.x + `ftrack-python-api>=3.1.0,<4.0.0`.
- Added explicit `ftrack-constants` dep and local uv sources for local monorepo resolution.
- Build flow validated using `tools/build.py` and installer command.

### Projects (`projects/*`)

All projects in `projects/` were migrated one-by-one to uv/PEP621/Hatch with:

- `version = "26.3.0.dev0"`
- `requires-python = ">= 3.13, < 3.14"`
- updated `ftrack-python-api` and internal lib ranges
- local `tool.uv.sources`
- local `uv.lock`
- README updated to uv commands and to run build commands from project directory

Migrated projects:

- `projects/rv`
- `projects/connect-publisher-widget`
- `projects/connect-timetracker-widget`
- `projects/framework-maya`
- `projects/framework-nuke`
- `projects/framework-max`
- `projects/framework-houdini`
- `projects/framework-harmony`
- `projects/framework-flame`
- `projects/framework-blender`
- `projects/framework-photoshop`
- `projects/framework-premiere`
- `projects/nuke-studio`

## Critical Decisions / Rules Followed

- Project migration cadence was one-by-one, with user approval checkpoints before moving on.
- Commit pattern after approval:
  - One commit per project migration checkpoint.
  - No push until explicitly requested.
- Build commands in READMEs standardized to run from project folders:
  - `cd integrations/projects/<project>`
  - `uv run python ../../tools/build.py ...`
- Photoshop and Premiere must include full flow, not just wheel/plugin build:
  - build qt-style CSS resources
  - build CEP (`--nosign` for local validation)
  - build connect plugin with CEP asset included

## Final Validation Performed

- `uv build` executed successfully for all migrated projects.
- Project-specific plugin flows were rerun and passed:
  - standard framework/connect plugin flows
  - `rv` flow includes `build_rvpkg` + plugin with `--include_assets`
  - `framework-photoshop` and `framework-premiere` full CEP flows with `--nosign`
- README audit against workflow behavior done, with special-step parity checked against `.github/workflows/build-plugin.yml`.

## Recent Migration Commit Sequence

- `d724ef243` feat(rv): migrate RV project to uv and refresh build pipeline
- `5ec80c046` feat(connect-publisher-widget): port project to uv and update build docs
- `82e222920` feat(connect-timetracker-widget): port project to uv and update build docs
- `140bd3247` docs(projects): run build script from project directories
- `540fa0ee2` feat(framework-maya): port project to uv with 26.3.0.dev0
- `36815702e` feat(framework-nuke): port project to uv with 26.3.0.dev0
- `15d50a5fb` feat(framework-max): port project to uv with 26.3.0.dev0
- `1c851491d` feat(framework-houdini): port project to uv with 26.3.0.dev0
- `f257f099e` feat(framework-harmony): port project to uv with 26.3.0.dev0
- `69d8a5f37` feat(framework-flame): port project to uv with 26.3.0.dev0
- `d66c0915c` feat(framework-blender): port project to uv with 26.3.0.dev0
- `be4914160` feat(framework-photoshop): port project and validate full cep build flow
- `3da2be02e` feat(framework-premiere): port project to uv with 26.3.0.dev0
- `30e076fb4` feat(nuke-studio): port project to uv with 26.3.0.dev0

## Known Local Untracked Artifacts (not committed)

There are local untracked files/folders from environment/build runs (examples):

- `.run/`, `.zed/`, `WARP.md`
- generated connect/build artifacts under `apps/connect/`
- generated style files under `resource/style/`
- generated rv artifacts under `projects/rv/`

These were intentionally left uncommitted.

## Suggested Next Steps (if continuing)

1. Open PR from `fi-7_use-uv-and-ruff-for-main-repo-management` and use this state as baseline.
2. If desired, add `.gitignore` entries for recurring local/generated artifacts.
3. If CI fails, compare failing job commands against README + `build-plugin.yml` patterns first.
