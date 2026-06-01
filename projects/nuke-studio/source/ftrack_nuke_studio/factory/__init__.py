# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Factory for creating ftrack task exporters with minimal boilerplate."""

from ftrack_nuke_studio.factory.task_factory import create_ftrack_task
from ftrack_nuke_studio.factory.resolver_utils import add_standard_resolvers

__all__ = [
    "create_ftrack_task",
    "add_standard_resolvers",
]
