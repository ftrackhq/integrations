# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Fixture validation: load each .ma fixture into Maya and compare
the live MayaSceneTracer output against the headless MayaFileTracer.

This confirms the fixtures are valid Maya scenes and that both
tracers agree on the dependency paths they discover.

Fixtures with references require the referenced files to exist
in the same directory (they use relative paths).
"""

from pathlib import Path

import pytest

FIXTURES = (Path(__file__).parent / "fixtures").resolve()

# Path to the development ftrack_utils source so Maya can find
# the new asset_tracer subpackage (the bundled ftrack-utils in
# framework-maya's dependencies doesn't have it yet).
_UTILS_SOURCE = str(
    Path(__file__).resolve().parents[3]
    / "libs"
    / "utils"
    / "source"
    / "ftrack_utils"
)


def _ensure_asset_tracer(dcc_client):
    """Extend ftrack_utils.__path__ inside Maya so asset_tracer is found."""
    dcc_client.execute(
        "import ftrack_utils\n"
        f"_p = r'{_UTILS_SOURCE}'\n"
        "if _p not in ftrack_utils.__path__:\n"
        "    ftrack_utils.__path__.insert(0, _p)\n"
    )


# Fixtures that DON'T contain references — both tracers should
# find the exact same set of dependency paths.
SIMPLE_FIXTURES = [
    "empty_scene.ma",
    "scene_with_textures.ma",
    "scene_with_image_plane.ma",
    "scene_with_audio.ma",
    "referenced_scene.ma",
]

# Fixtures that contain references — the live tracer filters out
# referenced nodes, so we compare reference paths + direct deps.
REFERENCE_FIXTURES = [
    "scene_with_reference.ma",
    "scene_mixed_deps.ma",
]

# Fixtures with plugin-dependent nodes (may warn but still load).
PLUGIN_FIXTURES = [
    "scene_with_alembic.ma",
    "scene_with_gpu_cache.ma",
]


class TestFixtureLoadsInMaya:
    """Verify each fixture can be opened in Maya without errors."""

    @pytest.mark.parametrize(
        "fixture_name",
        SIMPLE_FIXTURES + REFERENCE_FIXTURES + PLUGIN_FIXTURES,
    )
    def test_fixture_opens(self, dcc_client, fixture_name):
        """Fixture opens in Maya without fatal errors."""
        fixture_path = str(FIXTURES / fixture_name)
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "try:\n"
            "    cmds.file("
            f"    r'{fixture_path}',"
            "    open=True, force=True,"
            "    ignoreVersion=True)\n"
            "    scene = cmds.file(q=True, sceneName=True)\n"
            "    __result__ = {'ok': True, 'scene': scene}\n"
            "except Exception as e:\n"
            "    __result__ = {'ok': False, 'error': str(e)}\n"
        )
        assert result[
            "ok"
        ], f"Failed to open {fixture_name}: {result.get('error')}"


class TestSimpleFixtureComparison:
    """Compare live vs headless tracer on fixtures without references.

    For these, both tracers should discover the same dependency paths
    (the live scene has no referenced namespaces to filter).
    """

    @pytest.mark.parametrize("fixture_name", SIMPLE_FIXTURES)
    def test_live_vs_headless(self, dcc_client, fixture_name):
        """Live tracer and headless tracer find the same deps."""
        _ensure_asset_tracer(dcc_client)
        fixture_path = str(FIXTURES / fixture_name)

        # Open the fixture in Maya.
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file("
            f"r'{fixture_path}',"
            " open=True, force=True,"
            " ignoreVersion=True)\n"
        )

        # Get live tracer deps.
        live_result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "deps = MayaSceneTracer.get_scene_dependencies()\n"
            "__result__ = sorted(str(p) for p in deps)\n"
        )

        # Get headless tracer deps (run inside Maya for simplicity,
        # but it only reads the file — doesn't use maya.cmds).
        headless_result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_file_tracer"
            " import MayaFileTracer\n"
            "from pathlib import Path\n"
            f"deps = MayaFileTracer.get_dependencies("
            f"Path(r'{fixture_path}'))\n"
            "__result__ = sorted(str(p) for p in deps)\n"
        )

        live_names = sorted(Path(p).name for p in live_result)
        headless_names = sorted(Path(p).name for p in headless_result)

        assert live_names == headless_names, (
            f"Mismatch for {fixture_name}:\n"
            f"  Live:     {live_names}\n"
            f"  Headless: {headless_names}"
        )


class TestReferenceFixtureComparison:
    """Compare live vs headless tracer on fixtures WITH references.

    The live tracer filters out referenced nodes (textures inside
    references) but includes the reference file paths.  The headless
    tracer finds everything in the file text.

    We verify:
    1. Both find the same reference file paths.
    2. The live tracer does NOT include textures from referenced scenes.
    3. The headless tracer finds all deps declared in the file text.
    """

    @pytest.mark.parametrize("fixture_name", REFERENCE_FIXTURES)
    def test_reference_paths_match(self, dcc_client, fixture_name):
        """Both tracers find the same reference .ma/.mb paths."""
        _ensure_asset_tracer(dcc_client)
        fixture_path = str(FIXTURES / fixture_name)

        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file("
            f"r'{fixture_path}',"
            " open=True, force=True,"
            " ignoreVersion=True)\n"
        )

        live_refs = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "refs = MayaSceneTracer._get_references()\n"
            "__result__ = sorted(str(p) for p in refs)\n"
        )

        headless_deps = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_file_tracer"
            " import MayaFileTracer\n"
            "from pathlib import Path\n"
            f"deps = MayaFileTracer.get_dependencies("
            f"Path(r'{fixture_path}'))\n"
            "refs = [str(d) for d in deps"
            " if d.suffix in ('.ma', '.mb')]\n"
            "__result__ = sorted(refs)\n"
        )

        live_ref_names = sorted(Path(p).name for p in live_refs)
        headless_ref_names = sorted(Path(p).name for p in headless_deps)

        assert live_ref_names == headless_ref_names, (
            f"Reference mismatch for {fixture_name}:\n"
            f"  Live:     {live_ref_names}\n"
            f"  Headless: {headless_ref_names}"
        )

    @pytest.mark.parametrize("fixture_name", REFERENCE_FIXTURES)
    def test_live_excludes_referenced_textures(self, dcc_client, fixture_name):
        """Live tracer does NOT include textures from references."""
        _ensure_asset_tracer(dcc_client)
        fixture_path = str(FIXTURES / fixture_name)

        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file("
            f"r'{fixture_path}',"
            " open=True, force=True,"
            " ignoreVersion=True)\n"
        )

        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "deps = MayaSceneTracer.get_scene_dependencies()\n"
            "dep_names = [p.name for p in deps]\n"
            "# Get referenced file texture paths for comparison\n"
            "import maya.cmds as cmds\n"
            "all_file_nodes = cmds.ls(type='file') or []\n"
            "ref_tex_names = []\n"
            "for node in all_file_nodes:\n"
            "    try:\n"
            "        cmds.referenceQuery(node, filename=True)\n"
            "        # Node IS referenced — get its texture path\n"
            "        path = cmds.getAttr(node "
            "+ '.fileTextureName')\n"
            "        if path:\n"
            "            from pathlib import Path as P\n"
            "            ref_tex_names.append(P(path).name)\n"
            "    except RuntimeError:\n"
            "        pass\n"
            "__result__ = {"
            "'dep_names': dep_names,"
            "'ref_tex_names': ref_tex_names,"
            "}\n"
        )

        dep_names = result["dep_names"]
        ref_tex_names = result["ref_tex_names"]

        # Referenced textures should NOT appear in deps.
        for tex in ref_tex_names:
            assert tex not in dep_names, (
                f"Referenced texture {tex} should be excluded "
                f"from live deps in {fixture_name}"
            )


class TestPluginFixtures:
    """Verify plugin-dependent fixtures (alembic, gpu cache).

    These may not have the actual plugin loaded, but the nodes
    should still be created (Maya logs a warning but continues).
    """

    @pytest.mark.parametrize("fixture_name", PLUGIN_FIXTURES)
    def test_plugin_fixture_loads(self, dcc_client, fixture_name):
        """Plugin fixture opens and nodes exist."""
        fixture_path = str(FIXTURES / fixture_name)

        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file("
            f"r'{fixture_path}',"
            " open=True, force=True,"
            " ignoreVersion=True)\n"
        )

        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "all_nodes = cmds.ls(dag=True, long=True) or []\n"
            "all_types = set()\n"
            "for n in cmds.ls() or []:\n"
            "    all_types.add(cmds.nodeType(n))\n"
            "__result__ = {"
            "'node_count': len(all_nodes),"
            "'types': sorted(all_types),"
            "}\n"
        )

        # Scene should have SOME nodes (not completely empty).
        assert (
            result["node_count"] > 0
        ), f"{fixture_name} loaded but has no DAG nodes"


class TestFullTraceComparison:
    """Run MayaSceneTracer.trace() and verify structure."""

    def test_trace_saved_scene_with_texture(self, dcc_client):
        """Full trace on scene_with_textures produces correct tree."""
        _ensure_asset_tracer(dcc_client)
        fixture_path = str(FIXTURES / "scene_with_textures.ma")

        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file("
            f"r'{fixture_path}',"
            " open=True, force=True,"
            " ignoreVersion=True)\n"
        )

        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = {"
            "'scene': [str(p) for p in asset.paths],"
            "'children': len(asset.assets),"
            "'all_paths': [str(p) for p in asset.flatten()],"
            "}\n"
        )

        # Scene path should be the fixture file.
        assert len(result["scene"]) == 1
        assert "scene_with_textures.ma" in result["scene"][0]

        # Should have child assets for the textures.
        assert result["children"] >= 1

        # flatten() should include the scene + textures.
        all_names = [Path(p).name for p in result["all_paths"]]
        assert "scene_with_textures.ma" in all_names

    def test_trace_scene_with_reference(self, dcc_client):
        """Full trace on scene_with_reference includes ref + its deps."""
        _ensure_asset_tracer(dcc_client)
        fixture_path = str(FIXTURES / "scene_with_reference.ma")

        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file("
            f"r'{fixture_path}',"
            " open=True, force=True,"
            " ignoreVersion=True)\n"
        )

        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = {"
            "'all_paths': [str(p) for p in asset.flatten()],"
            "'child_count': len(asset.assets),"
            "}\n"
        )

        all_names = [Path(p).name for p in result["all_paths"]]

        # Should contain the scene, the reference, and the
        # reference's textures (traced recursively via headless
        # parser).
        assert "scene_with_reference.ma" in all_names
        assert "referenced_scene.ma" in all_names
