# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Utility functions for common token resolvers.

These resolvers are shared across most exporters, providing
standard tokens like {clip}, {shot}, {track}, {sequence}.
"""


def add_standard_resolvers(resolver):
    """Add common token resolvers used by most exporters.

    This adds the standard Hiero resolvers that are repeated
    in almost every exporter:
    - {clip} - Clip name
    - {shot} - Shot name
    - {track} - Track name
    - {sequence} - Sequence name

    Args:
        resolver: Hiero resolver object

    Example:
        >>> def addUserResolveEntries(self, resolver):
        ...     self.addFtrackResolveEntries(resolver)
        ...     add_standard_resolvers(resolver)
        ...     # Add custom resolvers...
    """
    resolver.addResolver(
        "{clip}",
        "Name of the clip used in the shot being processed",
        lambda keyword, task: task.clipName(),
    )

    resolver.addResolver(
        "{shot}",
        "Name of the shot being processed",
        lambda keyword, task: task.shotName(),
    )

    resolver.addResolver(
        "{track}",
        "Name of the track being processed",
        lambda keyword, task: task.trackName(),
    )

    resolver.addResolver(
        "{sequence}",
        "Name of the sequence being processed",
        lambda keyword, task: task.sequenceName(),
    )


def add_extension_resolver(resolver):
    """Add {ext} resolver for file extension.

    Args:
        resolver: Hiero resolver object

    Example:
        >>> def addUserResolveEntries(self, resolver):
        ...     add_standard_resolvers(resolver)
        ...     add_extension_resolver(resolver)
    """
    resolver.addResolver(
        "{ext}",
        "Extension of the file to be output",
        lambda keyword, task: task.fileext(),
    )
