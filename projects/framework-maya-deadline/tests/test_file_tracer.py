# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Tests for MayaFileTracer — headless .ma file parser.

These tests run without Maya, using minimal .ma fixture files.

Note: We import MayaFileTracer directly from its module file
(via importlib) to avoid triggering the main package __init__.py
which imports maya.cmds.
"""

import importlib.util
from pathlib import Path


from ftrack_utils.asset_tracer import TraceController

# Import MayaFileTracer without pulling in maya.cmds.
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

# Register so TraceController can dispatch .ma files.
TraceController.register_tracer([".ma"], MayaFileTracer)

FIXTURES = Path(__file__).parent / "fixtures"


class TestMayaFileTracerParse:
    """Verify MayaFileTracer.get_dependencies() on individual fixtures."""

    def test_parse_empty_scene(self):
        """Empty scene has no dependencies."""
        deps = MayaFileTracer.get_dependencies(FIXTURES / "empty_scene.ma")
        assert deps == []

    def test_parse_reference(self):
        """Reference to another .ma file is found."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_with_reference.ma"
        )
        assert len(deps) == 1
        assert deps[0].name == "referenced_scene.ma"

    def test_parse_file_texture(self):
        """File texture paths are found."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_with_textures.ma"
        )
        names = [p.name for p in deps]
        assert len(deps) == 3
        assert "diffuse_color.exr" in names
        assert "displacement.<UDIM>.exr" in names
        assert "roughness.tx" in names

    def test_parse_alembic(self):
        """AlembicNode cache path is found."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_with_alembic.ma"
        )
        assert len(deps) == 1
        assert deps[0] == Path("/cache/anim/character_v001.abc")

    def test_parse_gpu_cache(self):
        """gpuCache path is found."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_with_gpu_cache.ma"
        )
        assert len(deps) == 1
        assert deps[0] == Path("/cache/gpu/building_v002.abc")

    def test_parse_image_plane(self):
        """imagePlane path is found."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_with_image_plane.ma"
        )
        assert len(deps) == 1
        assert deps[0] == Path("/reference/storyboard_frame.tif")

    def test_parse_audio(self):
        """Audio node path is found."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_with_audio.ma"
        )
        assert len(deps) == 1
        assert deps[0] == Path("/audio/dialogue_take3.wav")

    def test_parse_mixed_deps(self):
        """Scene with mixed dependency types finds all of them."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_mixed_deps.ma"
        )
        names = [p.name for p in deps]
        # 2 references
        assert names.count("referenced_scene.ma") == 1
        assert names.count("scene_with_textures.ma") == 1
        # 3 textures
        assert "studio_hdri.exr" in names
        assert "ground_color.exr" in names
        assert "ground_displacement.<UDIM>.exr" in names
        # 1 alembic
        assert "shot010_v003.abc" in names
        # 1 audio
        assert "shot010_dialogue.wav" in names
        assert len(deps) == 7

    def test_parse_mb_reference(self):
        """Reference to .mb file is found."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_mb_reference.ma"
        )
        assert len(deps) == 1
        assert deps[0].name == "model.mb"

    def test_reference_not_matched_rdi(self):
        """file -rdi (reference depth info) is NOT double-matched.

        Both 'file -rdi' and 'file -r' lines contain the path,
        but only 'file -r' should be matched, so each reference
        appears exactly once.
        """
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_with_reference.ma"
        )
        # Only 1 reference, not 2 (rdi + r).
        assert len(deps) == 1

    def test_relative_path_resolved(self):
        """Relative paths in .ma files are resolved to fixture dir."""
        deps = MayaFileTracer.get_dependencies(
            FIXTURES / "scene_with_reference.ma"
        )
        # "referenced_scene.ma" is relative → resolved to fixtures/
        assert deps[0] == FIXTURES / "referenced_scene.ma"


class TestRecursiveTracing:
    """Verify TraceController recursive tracing with MayaFileTracer."""

    def test_recursive_reference(self):
        """scene_with_reference -> referenced_scene -> 2 textures."""
        asset = TraceController.trace(FIXTURES / "scene_with_reference.ma")

        flat = asset.flatten()
        names = [p.name for p in flat]

        # Root scene + referenced_scene + 2 textures = 4 paths
        assert "scene_with_reference.ma" in names
        assert "referenced_scene.ma" in names
        assert "diffuse.exr" in names
        assert "normal.exr" in names

    def test_nested_reference_chain(self):
        """nested_ref_chain -> scene_with_reference -> referenced_scene
        -> 2 textures.
        """
        asset = TraceController.trace(FIXTURES / "nested_ref_chain.ma")

        flat = asset.flatten()
        names = [p.name for p in flat]

        assert "nested_ref_chain.ma" in names
        assert "scene_with_reference.ma" in names
        assert "referenced_scene.ma" in names
        assert "diffuse.exr" in names
        assert "normal.exr" in names

    def test_cycle_detection(self):
        """Circular references terminate without infinite recursion."""
        asset = TraceController.trace(FIXTURES / "circular_ref_a.ma")

        flat = asset.flatten()
        names = [p.name for p in flat]

        assert "circular_ref_a.ma" in names
        assert "circular_ref_b.ma" in names
        # circular_ref_b references circular_ref_a which is already
        # in ancestors — recursion stops.
        assert len(flat) == 2

    def test_mb_is_leaf_node(self):
        """A .mb reference is returned as a leaf (no recursion)."""
        asset = TraceController.trace(FIXTURES / "scene_mb_reference.ma")

        flat = asset.flatten()
        names = [p.name for p in flat]

        assert "scene_mb_reference.ma" in names
        assert "model.mb" in names
        assert len(flat) == 2

    def test_mixed_deps_tree_structure(self):
        """scene_mixed_deps produces correct tree depth."""
        asset = TraceController.trace(FIXTURES / "scene_mixed_deps.ma")

        # Root should have children for each direct dependency.
        assert len(asset.assets) == 7

        flat = asset.flatten()
        # Root + 2 refs (each traced recursively) + 3 textures
        # + 1 alembic + 1 audio + deps from referenced scenes
        assert len(flat) > 7
