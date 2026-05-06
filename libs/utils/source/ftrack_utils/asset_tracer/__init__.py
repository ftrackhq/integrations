# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""
DCC-agnostic asset dependency tracer.

Provides an abstract interface for tracing file dependencies
in DCC scene files, with recursive resolution and cycle detection.

DCC-specific tracers (e.g., MayaFileTracer, UsdTracer) register
themselves via ``TraceController.register_tracer()`` and implement
``BaseTracer.get_dependencies()`` for their file types.
"""

from .base import BaseTracer
from .controller import TraceController
from .models import TracedAsset
from .tracers import DirectoryTracer, TextureTracer

__all__ = [
    "BaseTracer",
    "DirectoryTracer",
    "TextureTracer",
    "TraceController",
    "TracedAsset",
]
