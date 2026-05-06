# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Maya-specific asset tracers.

Registers :class:`MayaFileTracer` for ``.ma`` files so the
:class:`TraceController` can recursively trace Maya ASCII
references headlessly.
"""

from ftrack_utils.asset_tracer import (
    BaseTracer,
    TraceController,
    TracedAsset,
)

from .maya_file_tracer import MayaFileTracer

# Register the headless .ma parser so TraceController can
# recurse into Maya ASCII references automatically.
TraceController.register_tracer([".ma"], MayaFileTracer)

__all__ = [
    "BaseTracer",
    "MayaFileTracer",
    "TraceController",
    "TracedAsset",
]
