# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Built-in file-type tracers for common asset patterns."""

import logging
import os
from pathlib import Path

import clique

from .base import BaseTracer

logger = logging.getLogger(__name__)


class DirectoryTracer(BaseTracer):
    """Find file sequences inside a directory.

    Uses ``clique.assemble()`` to detect numbered sequences
    (e.g., ``render.0001.exr`` … ``render.0100.exr``) and returns
    one path per sequence using clique's collection format.
    """

    @classmethod
    def get_dependencies(cls, path: Path) -> list[Path]:
        """Return file sequences found in *path* (one level deep)."""
        if not path.is_dir():
            return []

        try:
            entries = os.listdir(str(path))
        except OSError as exc:
            logger.warning("DirectoryTracer: cannot list %s: %s", path, exc)
            return []

        collections, remainder = clique.assemble(entries, minimum_items=1)

        results: list[Path] = []
        for collection in collections:
            results.append(path / collection.format())
        for item in remainder:
            results.append(path / item)
        return results


class TextureTracer(BaseTracer):
    """Expand UDIM texture patterns to individual tile files.

    Expects a path containing a ``<UDIM>`` token.  Scans the
    parent directory for matching sequences with tile numbers
    >= 1001 (the standard UDIM range) and returns individual
    file paths.
    """

    @classmethod
    def get_dependencies(cls, path: Path) -> list[Path]:
        """Return individual tile files for a UDIM pattern."""
        path_str = str(path)
        if "<UDIM>" not in path_str:
            return []

        dir_path = path.parent
        if not dir_path.is_dir():
            logger.warning("TextureTracer: directory not found: %s", dir_path)
            return []

        try:
            entries = os.listdir(str(dir_path))
        except OSError as exc:
            logger.warning("TextureTracer: cannot list %s: %s", dir_path, exc)
            return []

        collections, _ = clique.assemble(entries, minimum_items=1)

        # Build the expected pattern by replacing <UDIM> with
        # clique's padding placeholder.
        target_head = path.name.split("<UDIM>")[0]
        target_tail = path.name.split("<UDIM>")[1]

        for collection in collections:
            head = collection.head
            tail = collection.tail
            if head == target_head and tail == target_tail:
                # Verify UDIM range (start >= 1001).
                indexes = list(collection.indexes)
                if indexes and min(indexes) >= 1001:
                    return [
                        dir_path / (head + str(idx) + tail) for idx in indexes
                    ]

        return []
