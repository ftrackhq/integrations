# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.engine import BaseEngine


class LoaderEngine(BaseEngine):
    """
    Base loader engine.

    Tool configs declare a flat `engine:` list using the canonical schema:
    a `context`-tagged plugin, one or more component groups (`type: group`,
    `tags: [component]`, plugins tagged `[collector|importer|post_importer]`),
    and a `finalizer`-tagged plugin. `BaseEngine.execute_engine` walks the
    list and respects per-group `enabled: False` for component selection.
    """

    name = "loader_engine"
    engine_types = ["loader"]
