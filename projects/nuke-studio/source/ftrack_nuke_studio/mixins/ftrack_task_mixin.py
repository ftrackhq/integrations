# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Mixin to add ftrack capabilities to Hiero tasks via composition.

Instead of inheriting from FtrackProcessor, tasks use this mixin
which composes the FtrackIntegration facade.
"""

from ftrack_nuke_studio.facade import FtrackIntegration
from ftrack_nuke_studio.session import get_shared_session


class FtrackTaskMixin:
    """Mixin to add ftrack capabilities to Hiero tasks via composition.

    This mixin uses composition instead of inheritance to add ftrack
    functionality. It should be mixed in with Hiero task classes.

    Example:
        >>> class FtrackCopyExporter(FtrackTaskMixin, CopyExporter):
        ...     def __init__(self, init_dict):
        ...         CopyExporter.__init__(self, init_dict)
        ...         self.__init_ftrack__(init_dict, self._preset.properties())

    Usage Pattern:
        1. Mix in FtrackTaskMixin before the Hiero base class
        2. Call __init_ftrack__() after parent __init__
        3. Use self._ftrack to access the facade
        4. Override component_name() if custom naming needed
    """

    def __init_ftrack__(self, init_dict, preset_properties):
        """Initialize ftrack integration.

        Call this from __init__ after parent class initialization.

        Args:
            init_dict: Hiero task init dict
            preset_properties: Preset properties dict containing 'ftrack' key

        Example:
            >>> def __init__(self, init_dict):
            ...     ParentExporter.__init__(self, init_dict)
            ...     self.__init_ftrack__(init_dict, self._preset.properties())
        """
        # Create integration facade
        self._ftrack = FtrackIntegration(
            session=get_shared_session(),
            preset_properties=preset_properties.get("ftrack", {}),
        )

        # Store reference to init dict
        self._init_dict = init_dict

    def component_name(self):
        """Return sanitized component name.

        Override in subclass if custom naming logic is needed.

        Returns:
            Sanitized component name safe for filesystem
        """
        return self._ftrack.path_service.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def _makePath(self):
        """Override to prevent Hiero's default path creation.

        ftrack will set paths via the facade's setup_task_paths callback.
        This disables Hiero's built-in path creation.
        """
        pass

    @property
    def session(self):
        """Access ftrack session.

        Returns:
            ftrack API session
        """
        return self._ftrack.session

    @property
    def ftrack_location(self):
        """Access ftrack location.

        Returns:
            ftrack Location entity
        """
        return self._ftrack.get_location()

    def sanitise_for_filesystem(self, value):
        """Sanitize value for filesystem use.

        Convenience method that delegates to path service.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string
        """
        return self._ftrack.path_service.sanitise_for_filesystem(value)
