# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Tests for MayaSceneTracer — live scene tracing inside Maya.

These tests require the dcc-test-harness and a running Maya
instance.  They verify that MayaSceneTracer correctly discovers
dependencies from the live scene graph.

Run via::

    cd /path/to/dcc-test-harness
    uv run python -m pytest /path/to/framework-maya-deadline/tests/test_tracer.py -v \\
        --dcc-connect-plugin /path/to/framework-maya/dist/... \\
        --dcc-connect-plugin /path/to/framework-maya-deadline
"""


def _ensure_bootstrap(dcc_client):
    """Force the deferred bootstrap to complete."""
    dcc_client.execute(
        "import ftrack_framework_maya_deadline\n"
        "ftrack_framework_maya_deadline.bootstrap()\n"
    )


class TestMayaSceneTracer:
    """Verify MayaSceneTracer tracing inside a live Maya session."""

    def test_empty_scene(self, dcc_client):
        """New empty scene returns empty TracedAsset."""
        _ensure_bootstrap(dcc_client)
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = {"
            "'paths': [str(p) for p in asset.paths],"
            "'child_count': len(asset.assets),"
            "'flat_count': len(asset.flatten()),"
            "}\n"
        )
        # Unsaved scene has no scene path.
        assert result["paths"] == []
        assert result["child_count"] == 0
        assert result["flat_count"] == 0

    def test_unsaved_scene(self, dcc_client):
        """Unsaved scene (file new) returns empty TracedAsset."""
        result = dcc_client.execute(
            "import maya.cmds as cmds\n"
            "cmds.file(new=True, force=True)\n"
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = len(asset.paths)\n"
        )
        assert result == 0

    def test_file_texture_traced(self, dcc_client):
        """File texture node path appears in trace result."""
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import tempfile, os\n"
            "cmds.file(new=True, force=True)\n"
            "p = os.path.join(tempfile.gettempdir(),"
            " 'tracer_test.ma')\n"
            "cmds.file(rename=p)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "node = cmds.shadingNode('file',"
            " asTexture=True)\n"
            "cmds.setAttr(node + '.fileTextureName',"
            " '/test/texture.exr', type='string')\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = [str(p) for p in asset.flatten()]\n"
        )
        assert "/test/texture.exr" in result

    def test_image_plane_traced(self, dcc_client):
        """Image plane path appears in trace result."""
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import tempfile, os\n"
            "cmds.file(new=True, force=True)\n"
            "p = os.path.join(tempfile.gettempdir(),"
            " 'tracer_imgplane.ma')\n"
            "cmds.file(rename=p)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "ip = cmds.createNode('imagePlane')\n"
            "cmds.setAttr(ip + '.imageName',"
            " '/test/bg_plate.tif', type='string')\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = [str(p) for p in asset.flatten()]\n"
        )
        assert "/test/bg_plate.tif" in result

    def test_audio_traced(self, dcc_client):
        """Audio node path appears in trace result."""
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import tempfile, os\n"
            "cmds.file(new=True, force=True)\n"
            "p = os.path.join(tempfile.gettempdir(),"
            " 'tracer_audio.ma')\n"
            "cmds.file(rename=p)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "node = cmds.createNode('audio')\n"
            "cmds.setAttr(node + '.filename',"
            " '/test/dialogue.wav', type='string')\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = [str(p) for p in asset.flatten()]\n"
        )
        assert "/test/dialogue.wav" in result

    def test_empty_path_skipped(self, dcc_client):
        """File node with empty path is not included in trace."""
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import tempfile, os\n"
            "cmds.file(new=True, force=True)\n"
            "p = os.path.join(tempfile.gettempdir(),"
            " 'tracer_empty.ma')\n"
            "cmds.file(rename=p)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "node = cmds.shadingNode('file',"
            " asTexture=True)\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "deps = MayaSceneTracer.get_scene_dependencies()\n"
            "__result__ = len(deps)\n"
        )
        # Empty fileTextureName should not be in deps.
        assert result == 0

    def test_reference_traced(self, dcc_client):
        """Referenced .ma file path appears in trace result."""
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import tempfile, os\n"
            "cmds.file(new=True, force=True)\n"
            "# Create a temp .ma to reference\n"
            "ref_path = os.path.join(tempfile.gettempdir(),"
            " 'tracer_ref_target.ma')\n"
            "cmds.file(rename=ref_path)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "# Create the main scene\n"
            "main_path = os.path.join(tempfile.gettempdir(),"
            " 'tracer_ref_main.ma')\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file(rename=main_path)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "# Add reference\n"
            "cmds.file(ref_path, reference=True,"
            " namespace='ref_ns')\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = [str(p) for p in asset.flatten()]\n"
        )
        assert any("tracer_ref_target.ma" in p for p in result)

    def test_referenced_texture_excluded(self, dcc_client):
        """Texture from a referenced scene is NOT in direct deps."""
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import tempfile, os\n"
            "# Create ref target with a texture node\n"
            "ref_path = os.path.join(tempfile.gettempdir(),"
            " 'tracer_reftex_target.ma')\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file(rename=ref_path)\n"
            "node = cmds.shadingNode('file',"
            " asTexture=True)\n"
            "cmds.setAttr(node + '.fileTextureName',"
            " '/ref/texture_inside_ref.exr', type='string')\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "# Create main scene and reference it\n"
            "main_path = os.path.join(tempfile.gettempdir(),"
            " 'tracer_reftex_main.ma')\n"
            "cmds.file(new=True, force=True)\n"
            "cmds.file(rename=main_path)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "cmds.file(ref_path, reference=True,"
            " namespace='reftex_ns')\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "deps = MayaSceneTracer.get_scene_dependencies()\n"
            "__result__ = [str(p) for p in deps]\n"
        )
        # The referenced .ma should be in deps...
        assert any("tracer_reftex_target.ma" in p for p in result)
        # ...but the texture inside it should NOT (it's referenced).
        assert not any("texture_inside_ref.exr" in p for p in result)

    def test_trace_returns_traced_asset(self, dcc_client):
        """trace() returns a properly structured TracedAsset."""
        dcc_client.execute(
            "import maya.cmds as cmds\n"
            "import tempfile, os\n"
            "cmds.file(new=True, force=True)\n"
            "p = os.path.join(tempfile.gettempdir(),"
            " 'tracer_struct.ma')\n"
            "cmds.file(rename=p)\n"
            "cmds.file(save=True, type='mayaAscii')\n"
            "node = cmds.shadingNode('file',"
            " asTexture=True)\n"
            "cmds.setAttr(node + '.fileTextureName',"
            " '/test/struct_tex.exr', type='string')\n"
        )
        result = dcc_client.execute(
            "from ftrack_framework_maya_deadline"
            ".tracer.maya_scene_tracer"
            " import MayaSceneTracer\n"
            "asset = MayaSceneTracer.trace()\n"
            "__result__ = {"
            "'has_paths': len(asset.paths) > 0,"
            "'has_assets': len(asset.assets) > 0,"
            "'scene_in_paths': 'tracer_struct.ma'"
            " in str(asset.paths[0]),"
            "'flat_count': len(asset.flatten()),"
            "}\n"
        )
        assert result["has_paths"] is True
        assert result["has_assets"] is True
        assert result["scene_in_paths"] is True
        assert result["flat_count"] >= 2  # scene + texture
