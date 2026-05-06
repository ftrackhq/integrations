# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Data models for the asset tracer."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TracedAsset:
    """A file asset and its recursive dependencies.

    Attributes:
        paths: File paths for this asset (usually one; may be
            multiple for sequence-type assets).
        assets: Child dependencies, each a ``TracedAsset`` that
            may itself have children, forming a tree.

    The tree can be flattened with :meth:`flatten` to get every
    path reachable from this node.
    """

    paths: list[Path] = field(default_factory=list)
    assets: list[TracedAsset] = field(default_factory=list)

    def flatten(self) -> list[Path]:
        """Return all paths from this asset and all descendants."""
        flat = list(self.paths)
        for child in self.assets:
            flat.extend(child.flatten())
        return flat
