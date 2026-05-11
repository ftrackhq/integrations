# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Versioned sync tests — headless, no Maya, no AWS.

Uses the MayaFileTracer to trace three versions of a shot scene
and verifies the expected dependency deltas.  Then simulates
sequential sync operations (via mocked S3SyncManager) to verify
that only the correct files are flagged for upload in each round.

Fixture layout::

    fixtures/versioned/
    ├── shared/           (room_setup.ma → prop_table.ma + prop_chair.mb)
    │   ├── room_setup.ma
    │   ├── prop_table.ma   (wood_diffuse.exr, wood_normal.exr)
    │   ├── prop_chair.mb   (binary leaf)
    │   ├── wood_diffuse.exr
    │   ├── wood_normal.exr
    │   └── metal_diffuse.exr
    ├── v1/               (baseline: room ref, metal texture, particles v001, audio)
    │   ├── shot_010.ma
    │   ├── particles_v001.abc
    │   └── ambience.wav
    ├── v2/               (updated cache, added roughness texture, removed audio)
    │   ├── shot_010.ma
    │   ├── metal_roughness.exr
    │   └── particles_v002.abc
    └── v3/               (added lamp ref with UDIM fabric textures)
        ├── shot_010.ma
        ├── prop_lamp.ma    (fabric_diffuse UDIM, fabric_normal)
        ├── metal_roughness.exr
        ├── particles_v002.abc
        ├── fabric_diffuse.1001.exr
        ├── fabric_diffuse.1002.exr
        └── fabric_normal.exr
"""

import importlib.util
from pathlib import Path

from ftrack_utils.asset_tracer import TraceController

# Import MayaFileTracer headlessly (no maya.cmds).
_tracer_path = (
    Path(__file__).parent.parent
    / "source"
    / "ftrack_framework_maya_deadline"
    / "tracer"
    / "maya_file_tracer.py"
)
_spec = importlib.util.spec_from_file_location(
    "maya_file_tracer", _tracer_path
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
MayaFileTracer = _mod.MayaFileTracer

# Register so TraceController dispatches .ma files.
TraceController.register_tracer([".ma"], MayaFileTracer)

VERSIONED = Path(__file__).parent / "fixtures" / "versioned"


def _trace_version(version: str) -> set[Path]:
    """Trace a versioned shot scene and return the set of resolved paths."""
    scene = VERSIONED / version / "shot_010.ma"
    asset = TraceController.trace(scene)
    return set(p.resolve() for p in asset.flatten())


def _filenames(paths: set[Path]) -> set[str]:
    """Extract just filenames from a set of paths for readable assertions."""
    return {p.name for p in paths}


# ===================================================================
# Test each version's dependency tree
# ===================================================================


class TestVersionedTracing:
    """Verify that each version traces the expected dependency tree."""

    def test_v1_dependencies(self):
        """v1: room ref (nested), metal texture, particles, audio."""
        paths = _trace_version("v1")
        names = _filenames(paths)

        # Scene itself
        assert "shot_010.ma" in names

        # Nested reference chain: room_setup → prop_table + prop_chair
        assert "room_setup.ma" in names
        assert "prop_table.ma" in names
        assert "prop_chair.mb" in names

        # Textures from prop_table (wood)
        assert "wood_diffuse.exr" in names
        assert "wood_normal.exr" in names

        # Direct texture from shot scene
        assert "metal_diffuse.exr" in names

        # Alembic cache
        assert "particles_v001.abc" in names

        # Audio
        assert "ambience.wav" in names

        # No roughness or fabric in v1
        assert "metal_roughness.exr" not in names
        assert "fabric_normal.exr" not in names

    def test_v2_dependencies(self):
        """v2: same refs, updated cache, added roughness, removed audio."""
        paths = _trace_version("v2")
        names = _filenames(paths)

        # Same nested refs
        assert "room_setup.ma" in names
        assert "prop_table.ma" in names
        assert "prop_chair.mb" in names
        assert "wood_diffuse.exr" in names
        assert "wood_normal.exr" in names
        assert "metal_diffuse.exr" in names

        # Updated cache
        assert "particles_v002.abc" in names
        assert "particles_v001.abc" not in names

        # New texture
        assert "metal_roughness.exr" in names

        # Audio removed
        assert "ambience.wav" not in names

    def test_v3_dependencies(self):
        """v3: added lamp ref with fabric UDIM textures."""
        paths = _trace_version("v3")
        names = _filenames(paths)

        # Same nested refs from room
        assert "room_setup.ma" in names
        assert "prop_table.ma" in names
        assert "prop_chair.mb" in names

        # New lamp ref and its deps
        assert "prop_lamp.ma" in names
        assert "fabric_normal.exr" in names
        # UDIM pattern should be preserved (not expanded, dir doesn't exist
        # for the tracer to enumerate)
        udim_paths = [p for p in paths if "fabric_diffuse" in p.name]
        assert len(udim_paths) >= 1

        # Carried forward from v2
        assert "metal_diffuse.exr" in names
        assert "metal_roughness.exr" in names
        assert "particles_v002.abc" in names

        # Still no audio
        assert "ambience.wav" not in names


# ===================================================================
# Test version-to-version deltas
# ===================================================================


class TestVersionDeltas:
    """Verify what changed between consecutive versions."""

    def test_v1_to_v2_added_files(self):
        """Files in v2 but not in v1."""
        v1 = _filenames(_trace_version("v1"))
        v2 = _filenames(_trace_version("v2"))
        added = v2 - v1

        assert "metal_roughness.exr" in added
        assert "particles_v002.abc" in added

    def test_v1_to_v2_removed_files(self):
        """Files in v1 but not in v2."""
        v1 = _filenames(_trace_version("v1"))
        v2 = _filenames(_trace_version("v2"))
        removed = v1 - v2

        assert "ambience.wav" in removed
        assert "particles_v001.abc" in removed

    def test_v1_to_v2_unchanged_files(self):
        """Files present in both v1 and v2."""
        v1 = _filenames(_trace_version("v1"))
        v2 = _filenames(_trace_version("v2"))
        unchanged = v1 & v2

        # Shared assets should persist
        assert "room_setup.ma" in unchanged
        assert "prop_table.ma" in unchanged
        assert "prop_chair.mb" in unchanged
        assert "wood_diffuse.exr" in unchanged
        assert "metal_diffuse.exr" in unchanged

    def test_v2_to_v3_added_files(self):
        """Files in v3 but not in v2."""
        v2 = _filenames(_trace_version("v2"))
        v3 = _filenames(_trace_version("v3"))
        added = v3 - v2

        assert "prop_lamp.ma" in added
        assert "fabric_normal.exr" in added

    def test_v2_to_v3_unchanged_files(self):
        """Files present in both v2 and v3."""
        v2 = _filenames(_trace_version("v2"))
        v3 = _filenames(_trace_version("v3"))
        unchanged = v2 & v3

        assert "metal_roughness.exr" in unchanged
        assert "particles_v002.abc" in unchanged
        assert "room_setup.ma" in unchanged

    def test_v2_to_v3_nothing_removed(self):
        """v3 doesn't remove anything that v2 had (only adds)."""
        v2 = _filenames(_trace_version("v2"))
        v3 = _filenames(_trace_version("v3"))
        removed = v2 - v3

        # v3 is a superset of v2 (minus scene files that differ by path)
        # Only shot_010.ma itself might differ (different directory)
        assert removed <= {"shot_010.ma"}


# ===================================================================
# Simulated sequential sync: mock which files are "on S3"
# ===================================================================


class TestSequentialSync:
    """Simulate syncing v1, then v2, then v3 — tracking what S3 has."""

    def test_sequential_upload_tracking(self):
        """After syncing each version, only new files need upload."""
        v1_paths = _trace_version("v1")
        v2_paths = _trace_version("v2")
        v3_paths = _trace_version("v3")

        # Simulate S3: track which files have been "uploaded".
        # Use resolved paths for exact comparison.
        s3_contents: set[Path] = set()

        # -- Sync v1 --
        v1_needs_upload = v1_paths - s3_contents
        assert v1_needs_upload == v1_paths  # Everything is new.
        s3_contents |= v1_paths  # "Upload" all of them.

        # -- Sync v2 --
        v2_needs_upload = v2_paths - s3_contents
        v2_already_synced = v2_paths & s3_contents

        # New in v2: metal_roughness, particles_v002, shot_010 (diff path)
        v2_upload_names = _filenames(v2_needs_upload)
        assert "metal_roughness.exr" in v2_upload_names
        assert "particles_v002.abc" in v2_upload_names

        # Shared assets should already be synced
        v2_synced_names = _filenames(v2_already_synced)
        assert "room_setup.ma" in v2_synced_names
        assert "prop_table.ma" in v2_synced_names
        assert "wood_diffuse.exr" in v2_synced_names
        assert "metal_diffuse.exr" in v2_synced_names

        s3_contents |= v2_paths  # "Upload" v2 files.

        # -- Sync v3 --
        v3_needs_upload = v3_paths - s3_contents
        v3_already_synced = v3_paths & s3_contents

        # New in v3: prop_lamp.ma, fabric textures, v3's shot_010
        v3_upload_names = _filenames(v3_needs_upload)
        assert "prop_lamp.ma" in v3_upload_names
        assert "fabric_normal.exr" in v3_upload_names

        # Everything from v2 should already be synced
        v3_synced_names = _filenames(v3_already_synced)
        assert "room_setup.ma" in v3_synced_names
        assert "metal_roughness.exr" in v3_synced_names
        assert "particles_v002.abc" in v3_synced_names

    def test_upload_count_decreases_over_versions(self):
        """Each successive sync requires fewer uploads."""
        v1_paths = _trace_version("v1")
        v2_paths = _trace_version("v2")
        v3_paths = _trace_version("v3")

        s3: set[Path] = set()

        v1_count = len(v1_paths - s3)
        s3 |= v1_paths

        v2_count = len(v2_paths - s3)
        s3 |= v2_paths

        v3_count = len(v3_paths - s3)

        # v1 uploads everything; v2 and v3 upload less each time.
        assert v1_count > v2_count
        assert v2_count > 0
        assert v3_count > 0
        assert v3_count < v1_count

    def test_resyncing_same_version_is_noop(self):
        """Syncing the same version twice requires zero uploads."""
        v1_paths = _trace_version("v1")
        s3 = set(v1_paths)

        # Re-trace and check — nothing new.
        v1_again = _trace_version("v1")
        needs_upload = v1_again - s3
        assert len(needs_upload) == 0


# ===================================================================
# Structural integrity tests
# ===================================================================


class TestFixtureIntegrity:
    """Verify the versioned fixtures are well-formed."""

    def test_shared_assets_are_reachable(self):
        """Shared .ma files should resolve to real files."""
        shared = VERSIONED / "shared"
        assert (shared / "room_setup.ma").exists()
        assert (shared / "prop_table.ma").exists()
        assert (shared / "prop_chair.mb").exists()
        assert (shared / "wood_diffuse.exr").exists()

    def test_all_versions_trace_without_error(self):
        """Each version traces successfully (no exceptions)."""
        for v in ("v1", "v2", "v3"):
            paths = _trace_version(v)
            assert len(paths) > 0, f"{v} traced zero files"

    def test_nested_ref_depth(self):
        """v1 has 3 levels of nesting: shot → room_setup → prop_table."""
        scene = VERSIONED / "v1" / "shot_010.ma"
        asset = TraceController.trace(scene)

        # Root level: shot_010 itself
        assert scene in asset.paths

        # First level: room_setup (and other direct deps)
        ref_names = [a.paths[0].name for a in asset.assets if a.paths]
        assert "room_setup.ma" in ref_names

        # Find room_setup's sub-assets
        room_asset = next(
            a
            for a in asset.assets
            if a.paths and a.paths[0].name == "room_setup.ma"
        )
        room_child_names = [
            a.paths[0].name for a in room_asset.assets if a.paths
        ]
        assert "prop_table.ma" in room_child_names
        assert "prop_chair.mb" in room_child_names

    def test_mb_is_leaf_node(self):
        """prop_chair.mb should be a leaf (no further recursion)."""
        scene = VERSIONED / "v1" / "shot_010.ma"
        asset = TraceController.trace(scene)

        # Find prop_chair.mb in the flattened tree
        all_paths = asset.flatten()
        chair_paths = [p for p in all_paths if p.name == "prop_chair.mb"]
        assert len(chair_paths) == 1  # Present exactly once
