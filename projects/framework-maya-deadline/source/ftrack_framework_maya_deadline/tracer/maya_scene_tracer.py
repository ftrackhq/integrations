# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Live Maya scene tracer using maya.cmds.

Queries the currently open Maya scene graph to discover all
direct file dependencies.  Returns only non-referenced nodes
so that the :class:`TraceController` can recursively trace
each reference file without double-counting.
"""

import logging
from pathlib import Path

import maya.cmds as cmds

from ftrack_utils.asset_tracer import TraceController, TracedAsset

logger = logging.getLogger(__name__)


class MayaSceneTracer:
    """Trace dependencies from the currently open Maya scene.

    Uses ``maya.cmds`` to query the live scene graph for
    references, file textures, alembic caches, GPU caches,
    image planes, and audio nodes.

    Example::

        asset = MayaSceneTracer.trace()
        for path in asset.flatten():
            print(path)
    """

    @classmethod
    def trace(cls) -> TracedAsset:
        """Trace the currently open Maya scene.

        Returns a :class:`TracedAsset` rooted at the scene file
        with recursively traced children.  Returns an empty
        ``TracedAsset`` if the scene is unsaved.
        """
        scene_path = cmds.file(q=True, sceneName=True)
        if not scene_path:
            logger.debug("No scene file open (unsaved scene)")
            return TracedAsset()

        deps = cls.get_scene_dependencies()
        logger.info(
            "MayaSceneTracer: %d direct dependencies from %s",
            len(deps),
            scene_path,
        )
        return TraceController.trace_live(Path(scene_path), deps)

    @classmethod
    def get_scene_dependencies(cls) -> list[Path]:
        """Return all direct file dependencies from the live scene.

        Only returns dependencies from non-referenced nodes.
        Referenced scenes are returned as paths (so the controller
        can recurse into them), but their internal file nodes are
        skipped to avoid double-counting.
        """
        deps: list[Path] = []
        deps.extend(cls._get_references())
        deps.extend(cls._get_file_textures())
        deps.extend(cls._get_alembic_caches())
        deps.extend(cls._get_gpu_caches())
        deps.extend(cls._get_image_planes())
        deps.extend(cls._get_audio())
        return deps

    # -- Reference discovery --

    @classmethod
    def _get_references(cls) -> list[Path]:
        """Return paths of all referenced files (.ma/.mb)."""
        refs = cmds.file(q=True, reference=True) or []
        results: list[Path] = []
        for ref in refs:
            try:
                resolved = cmds.referenceQuery(
                    ref, filename=True, withoutCopyNumber=True
                )
                if resolved:
                    results.append(Path(resolved))
            except RuntimeError:
                logger.debug("Could not query reference: %s", ref)
        return results

    # -- Node attribute helpers --

    @classmethod
    def _is_referenced(cls, node: str) -> bool:
        """Return True if *node* belongs to a file reference."""
        try:
            cmds.referenceQuery(node, filename=True)
            return True
        except RuntimeError:
            return False

    @classmethod
    def _get_attr_paths(
        cls,
        node_type: str,
        attr_name: str,
    ) -> list[Path]:
        """Query all nodes of *node_type* for *attr_name*.

        Skips referenced nodes and empty/missing attributes.
        """
        try:
            nodes = cmds.ls(type=node_type) or []
        except RuntimeError:
            # Node type unknown (plugin not loaded).
            return []

        results: list[Path] = []
        for node in nodes:
            if cls._is_referenced(node):
                continue
            try:
                value = cmds.getAttr("{}.{}".format(node, attr_name))
            except (ValueError, RuntimeError):
                continue
            if value:
                results.append(Path(value))
        return results

    # -- Per-type discovery methods --

    @classmethod
    def _get_file_textures(cls) -> list[Path]:
        """Return paths from non-referenced file texture nodes."""
        return cls._get_attr_paths("file", "fileTextureName")

    @classmethod
    def _get_alembic_caches(cls) -> list[Path]:
        """Return paths from non-referenced AlembicNode nodes."""
        return cls._get_attr_paths("AlembicNode", "abc_File")

    @classmethod
    def _get_gpu_caches(cls) -> list[Path]:
        """Return paths from non-referenced gpuCache nodes."""
        return cls._get_attr_paths("gpuCache", "cacheFileName")

    @classmethod
    def _get_image_planes(cls) -> list[Path]:
        """Return paths from non-referenced imagePlane nodes."""
        return cls._get_attr_paths("imagePlane", "imageName")

    @classmethod
    def _get_audio(cls) -> list[Path]:
        """Return paths from non-referenced audio nodes."""
        return cls._get_attr_paths("audio", "filename")
