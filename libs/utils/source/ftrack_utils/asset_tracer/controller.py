# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Trace controller for recursive file dependency resolution."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .base import BaseTracer
from .models import TracedAsset
from .tracers import DirectoryTracer, TextureTracer

logger = logging.getLogger(__name__)


class TraceController:
    """Recursively trace file dependencies.

    DCC plugins register their file tracers via
    :meth:`register_tracer`.  The controller dispatches to the
    appropriate tracer based on file extension and recursively
    builds a :class:`TracedAsset` tree.

    Two entry points:

    * :meth:`trace` — headless, starts from a file path on disk.
    * :meth:`trace_live` — for DCC plugins that have already
      queried the live scene graph for direct dependencies.
    """

    _tracer_registry: dict[str, type[BaseTracer]] = {}

    @classmethod
    def register_tracer(
        cls,
        extensions: list[str],
        tracer: type[BaseTracer],
    ) -> None:
        """Register *tracer* for the given file *extensions*.

        Args:
            extensions: File suffixes including the dot
                (e.g., ``[".ma", ".mb"]``).
            tracer: A :class:`BaseTracer` subclass.
        """
        for ext in extensions:
            cls._tracer_registry[ext] = tracer
            logger.debug("Registered tracer %s for %s", tracer.__name__, ext)

    @classmethod
    def select_tracer(cls, path: Path) -> type[BaseTracer]:
        """Choose the tracer for *path* based on its type.

        Checks the registry first, then falls back to built-in
        tracers for directories and UDIM textures.  Returns
        :class:`BaseTracer` (a leaf node) if no match.
        """
        if path.is_dir():
            return DirectoryTracer

        if path.suffix in cls._tracer_registry:
            return cls._tracer_registry[path.suffix]

        if path.suffix in (
            ".exr",
            ".png",
            ".tif",
            ".tiff",
        ) and "<UDIM>" in str(path):
            return TextureTracer

        return BaseTracer

    @classmethod
    def trace(cls, entrypoint: Path) -> TracedAsset:
        """Recursively trace *entrypoint* and all its dependencies.

        Builds a :class:`TracedAsset` tree with cycle detection
        via an ancestors list.
        """
        return cls._recurse(entrypoint, [])

    @classmethod
    def trace_live(
        cls,
        scene_path: Path,
        dependencies: list[Path],
    ) -> TracedAsset:
        """Build a :class:`TracedAsset` tree from pre-discovered deps.

        Used by DCC plugins that query the live scene graph
        (e.g., ``MayaSceneTracer``).  The plugin provides the
        scene path and its direct dependencies; this method
        recursively traces each dependency using registered
        file tracers.

        Args:
            scene_path: The scene file path.
            dependencies: Direct dependencies discovered by the
                DCC-specific tracer.

        Returns:
            A :class:`TracedAsset` rooted at *scene_path* with
            recursively traced children.
        """
        children: list[TracedAsset] = []
        ancestors: list[Any] = [scene_path]
        for dep in dependencies:
            if dep not in ancestors:
                children.append(cls._recurse(dep, ancestors))
        return TracedAsset(paths=[scene_path], assets=children)

    @classmethod
    def _recurse(
        cls,
        current: Path,
        ancestors: list[Any],
    ) -> TracedAsset:
        """Recursively trace *current*, tracking *ancestors* for cycles."""
        ancestors.append(current)
        child_assets: list[TracedAsset] = []

        try:
            tracer = cls.select_tracer(current)
            dependencies = tracer.get_dependencies(current)

            for dependency in dependencies:
                if dependency in ancestors:
                    logger.debug(
                        "Cycle detected: %s already in ancestors, " "skipping",
                        dependency,
                    )
                    continue

                sub_tracer = cls.select_tracer(dependency)
                if sub_tracer in (DirectoryTracer, TextureTracer):
                    # These return lists of paths — expand inline.
                    sub_deps = sub_tracer.get_dependencies(dependency)
                    if sub_deps:
                        for sub_dep in sub_deps:
                            if sub_dep in ancestors:
                                continue
                            child_assets.append(
                                cls._recurse(sub_dep, ancestors)
                            )
                    else:
                        # Expansion returned nothing (e.g., UDIM dir
                        # doesn't exist).  Preserve original path as
                        # a leaf so it isn't silently lost.
                        child_assets.append(
                            TracedAsset(paths=[dependency], assets=[])
                        )
                else:
                    child_assets.append(cls._recurse(dependency, ancestors))

        except NotImplementedError:
            # Can't trace further — return as leaf node.
            return TracedAsset(paths=[current], assets=[])

        except FileNotFoundError:
            # Preserve the path so download flows can detect it as missing.
            logger.debug("File not found (preserving path): %s", current)
            return TracedAsset(paths=[current], assets=[])

        return TracedAsset(paths=[current], assets=child_assets)
