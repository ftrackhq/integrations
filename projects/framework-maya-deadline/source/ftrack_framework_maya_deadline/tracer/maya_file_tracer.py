# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Headless Maya ASCII (.ma) file parser.

Extracts file dependencies from ``.ma`` files using regex,
without requiring a running Maya instance.  Used by the
:class:`TraceController` for recursive reference following.

Limitations:
    - ``.mb`` (Maya Binary) files cannot be parsed headlessly.
      They are treated as leaf nodes by the controller.
    - Multi-line MEL strings are rare and not handled.
    - MEL variable paths (e.g., ``$ASSET_DIR/texture.exr``)
      are returned as-is, not resolved.
"""

import logging
import re
from pathlib import Path

from ftrack_utils.asset_tracer.base import BaseTracer

logger = logging.getLogger(__name__)


class MayaFileTracer(BaseTracer):
    """Parse Maya ASCII files to extract file dependencies.

    Matches ``file -r`` commands (references) and ``setAttr``
    commands that set file path attributes on common node types:
    file textures, AlembicNode, gpuCache, imagePlane, and audio.
    """

    # file -r (reference), but NOT file -rdi (reference depth info
    # metadata).  ``-r\s`` matches "-r " but not "-rdi" because
    # the \s requires whitespace immediately after -r.
    # Uses re.DOTALL so .*? can cross line breaks (file -r commands
    # in .ma files often span multiple lines with tab continuation).
    REFERENCE_RE = re.compile(
        r'file\s+-r\s.*?"([^"]+\.m[ab])"\s*;',
        re.DOTALL,
    )

    # setAttr patterns use \s+ between tokens to handle both
    # single-line and multi-line attribute declarations.
    FILE_TEXTURE_RE = re.compile(
        r'setAttr\s+"[^"]*\.fileTextureName"\s+'
        r'-type\s+"string"\s+"([^"]+)"',
    )

    ALEMBIC_RE = re.compile(
        r'setAttr\s+"[^"]*\.abc_File"\s+' r'-type\s+"string"\s+"([^"]+)"',
    )

    GPU_CACHE_RE = re.compile(
        r'setAttr\s+"[^"]*\.cacheFileName"\s+' r'-type\s+"string"\s+"([^"]+)"',
    )

    IMAGE_PLANE_RE = re.compile(
        r'setAttr\s+"[^"]*\.imageName"\s+' r'-type\s+"string"\s+"([^"]+)"',
    )

    AUDIO_RE = re.compile(
        r'setAttr\s+"[^"]*\.filename"\s+' r'-type\s+"string"\s+"([^"]+)"',
    )

    @classmethod
    def _all_patterns(cls) -> list[re.Pattern]:
        """Return all regex patterns used for dependency extraction."""
        return [
            cls.REFERENCE_RE,
            cls.FILE_TEXTURE_RE,
            cls.ALEMBIC_RE,
            cls.GPU_CACHE_RE,
            cls.IMAGE_PLANE_RE,
            cls.AUDIO_RE,
        ]

    @classmethod
    def get_dependencies(cls, path: Path) -> list[Path]:
        """Parse a ``.ma`` file and return all file dependencies.

        Args:
            path: Path to a Maya ASCII file.

        Returns:
            List of dependency file paths found in the file.
            Relative paths are resolved relative to the ``.ma``
            file's parent directory.
        """
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            raise
        except OSError as exc:
            logger.warning("MayaFileTracer: cannot read %s: %s", path, exc)
            return []

        deps: list[Path] = []
        for pattern in cls._all_patterns():
            for match in pattern.findall(text):
                dep_path = Path(match)
                # Resolve relative paths against the .ma file's dir.
                if not dep_path.is_absolute():
                    dep_path = path.parent / dep_path
                deps.append(dep_path)

        if deps:
            logger.debug(
                "MayaFileTracer: %s -> %d dependencies",
                path,
                len(deps),
            )

        return deps
