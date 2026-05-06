# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Unit tests for ftrack_utils.asset_tracer.

These tests run without any DCC (no Maya, Nuke, etc.).
They verify the core TracedAsset model, the TraceController
dispatch and recursion logic, and tracer registration.
"""

from pathlib import Path


from ftrack_utils.asset_tracer import (
    BaseTracer,
    TraceController,
    TracedAsset,
)


# -- TracedAsset model tests --


class TestTracedAsset:
    """Verify TracedAsset dataclass and flatten()."""

    def test_empty_asset(self):
        """Empty TracedAsset has no paths."""
        asset = TracedAsset()
        assert asset.paths == []
        assert asset.assets == []
        assert asset.flatten() == []

    def test_single_path(self):
        """Asset with one path returns it from flatten()."""
        asset = TracedAsset(paths=[Path("/a/file.exr")])
        assert asset.flatten() == [Path("/a/file.exr")]

    def test_flatten_nested(self):
        """flatten() collects paths from all levels of the tree."""
        root = TracedAsset(
            paths=[Path("/scene.ma")],
            assets=[
                TracedAsset(
                    paths=[Path("/ref.ma")],
                    assets=[
                        TracedAsset(paths=[Path("/tex/a.exr")]),
                        TracedAsset(paths=[Path("/tex/b.exr")]),
                    ],
                ),
                TracedAsset(paths=[Path("/cache.abc")]),
            ],
        )
        flat = root.flatten()
        assert len(flat) == 5
        assert Path("/scene.ma") in flat
        assert Path("/ref.ma") in flat
        assert Path("/tex/a.exr") in flat
        assert Path("/tex/b.exr") in flat
        assert Path("/cache.abc") in flat

    def test_flatten_preserves_order(self):
        """flatten() returns paths in depth-first order."""
        root = TracedAsset(
            paths=[Path("/root")],
            assets=[
                TracedAsset(
                    paths=[Path("/child1")],
                    assets=[
                        TracedAsset(paths=[Path("/grandchild")]),
                    ],
                ),
                TracedAsset(paths=[Path("/child2")]),
            ],
        )
        flat = root.flatten()
        assert flat == [
            Path("/root"),
            Path("/child1"),
            Path("/grandchild"),
            Path("/child2"),
        ]


# -- Helpers for controller tests --


class _StubTracer(BaseTracer):
    """Tracer that returns pre-configured dependencies."""

    _deps: dict[str, list[str]] = {}

    @classmethod
    def set_deps(cls, mapping: dict[str, list[str]]):
        cls._deps = mapping

    @classmethod
    def get_dependencies(cls, path: Path) -> list[Path]:
        key = str(path)
        if key in cls._deps:
            return [Path(d) for d in cls._deps[key]]
        return []


# -- TraceController tests --


class TestTraceController:
    """Verify tracer registration, dispatch, and recursion."""

    def setup_method(self):
        """Clean the registry before each test."""
        TraceController._tracer_registry.clear()
        _StubTracer._deps = {}

    def test_register_and_select(self):
        """Registered tracer is returned by select_tracer()."""
        TraceController.register_tracer([".stub"], _StubTracer)
        result = TraceController.select_tracer(Path("/a/file.stub"))
        assert result is _StubTracer

    def test_select_fallback(self):
        """Unknown extension returns BaseTracer."""
        result = TraceController.select_tracer(Path("/a/file.unknown"))
        assert result is BaseTracer

    def test_select_udim_texture(self):
        """UDIM .exr path routes to TextureTracer."""
        from ftrack_utils.asset_tracer import TextureTracer

        path = Path("/tex/color.<UDIM>.exr")
        result = TraceController.select_tracer(path)
        assert result is TextureTracer

    def test_select_directory(self, tmp_path):
        """Directory routes to DirectoryTracer."""
        from ftrack_utils.asset_tracer import DirectoryTracer

        result = TraceController.select_tracer(tmp_path)
        assert result is DirectoryTracer

    def test_registered_takes_priority(self):
        """Registry entry overrides built-in UDIM check."""
        TraceController.register_tracer([".exr"], _StubTracer)
        path = Path("/tex/color.<UDIM>.exr")
        result = TraceController.select_tracer(path)
        assert result is _StubTracer

    def test_trace_leaf_node(self):
        """Tracing a file with no registered tracer returns leaf."""
        asset = TraceController.trace(Path("/some/texture.exr"))
        assert len(asset.paths) == 1
        assert asset.assets == []

    def test_trace_missing_file(self):
        """Tracing a nonexistent file with a registered tracer."""
        TraceController.register_tracer([".stub"], _StubTracer)
        _StubTracer.set_deps({})
        # File doesn't exist but the stub tracer returns no deps.
        asset = TraceController.trace(Path("/nonexistent.stub"))
        assert asset.paths == [Path("/nonexistent.stub")]
        assert asset.assets == []

    def test_trace_recursive(self, tmp_path):
        """Controller recursively traces via registered tracer."""
        # Create real files so FileNotFoundError isn't raised.
        a = tmp_path / "a.stub"
        b = tmp_path / "b.stub"
        c = tmp_path / "c.txt"
        d = tmp_path / "d.txt"
        a.write_text("")
        b.write_text("")
        c.write_text("")
        d.write_text("")

        TraceController.register_tracer([".stub"], _StubTracer)
        _StubTracer.set_deps(
            {
                str(a): [str(b), str(d)],
                str(b): [str(c)],
            }
        )

        asset = TraceController.trace(a)

        # a -> [b -> [c], d]
        assert asset.paths == [a]
        assert len(asset.assets) == 2
        flat = asset.flatten()
        assert a in flat
        assert b in flat
        assert c in flat
        assert d in flat

    def test_trace_cycle_detection(self, tmp_path):
        """Circular dependencies don't cause infinite recursion."""
        a = tmp_path / "a.stub"
        b = tmp_path / "b.stub"
        a.write_text("")
        b.write_text("")

        TraceController.register_tracer([".stub"], _StubTracer)
        _StubTracer.set_deps(
            {
                str(a): [str(b)],
                str(b): [str(a)],  # cycle!
            }
        )

        asset = TraceController.trace(a)

        # a -> b -> (a skipped due to cycle detection)
        flat = asset.flatten()
        assert a in flat
        assert b in flat
        # Should NOT recurse infinitely.
        assert len(flat) == 2

    def test_trace_live(self, tmp_path):
        """trace_live() builds tree from pre-discovered deps."""
        scene = tmp_path / "scene.ma"
        tex1 = tmp_path / "tex1.exr"
        tex2 = tmp_path / "tex2.exr"
        scene.write_text("")
        tex1.write_text("")
        tex2.write_text("")

        asset = TraceController.trace_live(scene, [tex1, tex2])

        assert asset.paths == [scene]
        assert len(asset.assets) == 2
        flat = asset.flatten()
        assert scene in flat
        assert tex1 in flat
        assert tex2 in flat

    def test_trace_live_skips_duplicates(self, tmp_path):
        """trace_live() skips deps that match scene_path."""
        scene = tmp_path / "scene.ma"
        scene.write_text("")

        asset = TraceController.trace_live(
            scene,
            [scene],  # scene references itself
        )

        assert asset.paths == [scene]
        assert len(asset.assets) == 0
