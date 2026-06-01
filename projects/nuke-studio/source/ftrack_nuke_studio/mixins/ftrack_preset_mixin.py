# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Mixin for ftrack preset functionality.

Provides preset-level ftrack functionality using composition.
"""

from ftrack_nuke_studio.facade import FtrackIntegration
from ftrack_nuke_studio.session import get_shared_session
from ftrack_nuke_studio.exception import FtrackLocationError


class FtrackPresetMixin:
    """Mixin for ftrack preset functionality.

    This mixin adds ftrack-specific preset initialization and resolvers.
    It uses composition to access ftrack functionality.

    Example:
        >>> class FtrackCopyExporterPreset(FtrackPresetMixin, CopyPreset):
        ...     def __init__(self, name, properties):
        ...         CopyPreset.__init__(self, name, properties)
        ...         self.__init_ftrack__(name, properties)

    Usage Pattern:
        1. Mix in FtrackPresetMixin before the Hiero base class
        2. Call __init_ftrack__() after parent __init__
        3. Override set_ftrack_properties() to set task-specific defaults
        4. Call addFtrackResolveEntries() from addUserResolveEntries()
    """

    # Invalid location names that shouldn't be used
    IGNORED_LOCATIONS = [
        "ftrack.server",
        "ftrack.review",
        "ftrack.origin",
        "ftrack.unmanaged",
        "ftrack.connect",
        "ftrack.perforce-scenario",
    ]

    def __init_ftrack__(self, name, properties):
        """Initialize ftrack preset.

        Call from __init__ after parent initialization.

        Args:
            name: Preset name
            properties: Preset properties dict

        Raises:
            FtrackLocationError: If location is invalid

        Example:
            >>> def __init__(self, name, properties):
            ...     ParentPreset.__init__(self, name, properties)
            ...     self.__init_ftrack__(name, properties)
        """
        # Initialize ftrack properties if not present
        if not properties.get("ftrack"):
            self.set_ftrack_properties(properties)

        # Validate location
        session = get_shared_session()
        location = session.pick_location()

        if location["name"] in self.IGNORED_LOCATIONS:
            raise FtrackLocationError(
                location["name"],
                reason=(
                    "This location is not valid for Nuke Studio. "
                    "Please setup a centralized storage scenario or custom location."
                ),
            )

        # Set export root to location prefix
        if "exportRoot" not in properties:
            properties["exportRoot"] = location.accessor.prefix

    def set_ftrack_properties(self, properties):
        """Set default ftrack properties.

        Override in subclass to set task-specific defaults.
        This base implementation sets common defaults.

        Args:
            properties: Properties dict to update
        """
        properties.setdefault("ftrack", {})
        properties["ftrack"]["opt_publish_reviewable"] = True
        properties["ftrack"]["opt_publish_thumbnail"] = False
        properties["useAssets"] = False
        properties["keepNukeScript"] = True

    def addFtrackResolveEntries(self, resolver):
        """Add ftrack token resolvers.

        Call from addCustomResolveEntries/addUserResolveEntries.

        Args:
            resolver: Hiero resolver object

        Example:
            >>> def addUserResolveEntries(self, resolver):
            ...     self.addFtrackResolveEntries(resolver)
            ...     # Add task-specific resolvers...
        """
        # Create temporary integration for resolver access
        # This is lightweight - just for accessing path service
        integration = FtrackIntegration(
            get_shared_session(), self.properties()["ftrack"]
        )

        # Add ftrack resolvers
        resolver.addResolver(
            "{ftrack_project_structure}",
            "Ftrack context (Project/Episodes/Sequence/Shots)",
            lambda k, t: self._resolve_project_structure(t, integration),
        )

        resolver.addResolver(
            "{ftrack_version}",
            "Ftrack version (v001, v002, etc)",
            lambda k, t: self._resolve_version(t, integration),
        )

        resolver.addResolver(
            "{ftrack_component}",
            "Ftrack component name",
            lambda k, t: self._resolve_component(t, integration),
        )

    def _resolve_project_structure(self, task, integration):
        """Resolve {ftrack_project_structure} token.

        Args:
            task: Hiero task
            integration: FtrackIntegration instance

        Returns:
            Composed name string or None
        """
        import os
        from ftrack_nuke_studio.template import get_project_template

        project_id = os.getenv("FTRACK_CONTEXTID")
        ftrack_project = integration.session.get("Project", project_id)
        ftrack_project_name = ftrack_project["full_name"]

        template = get_project_template(task._project)

        return integration.path_service.resolve_project_structure(
            task, template, ftrack_project_name
        )

    def _resolve_version(self, task, integration):
        """Resolve {ftrack_version} token.

        Args:
            task: Hiero task
            integration: FtrackIntegration instance

        Returns:
            Version string (v001, v002, etc)
        """
        return integration.path_service.resolve_version(
            task, integration.registry
        )

    def _resolve_component(self, task, integration):
        """Resolve {ftrack_component} token.

        Args:
            task: Hiero task
            integration: FtrackIntegration instance

        Returns:
            Component filename
        """
        component_pattern = self.properties()["ftrack"]["component_pattern"]
        return integration.path_service.resolve_component(
            task, component_pattern
        )
