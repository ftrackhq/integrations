# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Abstract base class for file-type tracers."""

from abc import ABCMeta, abstractmethod
from pathlib import Path


class BaseTracer(metaclass=ABCMeta):
    """Abstract tracer that extracts file dependencies from an asset.

    Subclasses implement :meth:`get_dependencies` for a specific
    file type (e.g., Maya ASCII, USD, Blender).  The
    :class:`TraceController` calls this method during recursive
    dependency resolution.
    """

    @classmethod
    @abstractmethod
    def get_dependencies(cls, path: Path) -> list[Path]:
        """Return file paths that *path* depends on.

        Args:
            path: The file to inspect.

        Returns:
            A list of dependency file paths.  An empty list means
            the file is a leaf node with no further dependencies.

        Raises:
            NotImplementedError: If the file type cannot be traced
                (the controller treats this as a leaf node).
        """
        raise NotImplementedError()
