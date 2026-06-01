# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Service for path template resolution.

This service handles:
- Parsing and resolving path templates
- Generating ftrack structure paths
- Component naming patterns
- Filesystem name sanitization
"""

import os
import re
import unicodedata
import logging


class PathResolutionService:
    """Service for path template resolution.

    Extracted from FtrackProcessor and FtrackBasePreset to centralize
    path resolution logic.
    """

    def __init__(
        self, location, illegal_character_substitute="_", path_separator="/"
    ):
        """Initialize service with ftrack location.

        Args:
            location: ftrack Location entity
            illegal_character_substitute: Character to replace invalid chars with
            path_separator: Path separator character (default '/')
        """
        self.location = location
        self.illegal_character_substitute = illegal_character_substitute
        self.path_separator = path_separator
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

    def sanitise_for_filesystem(self, value):
        """Replace illegal filesystem characters.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string safe for filesystem use
        """
        if self.illegal_character_substitute is None:
            return value

        if isinstance(value, bytes):
            value = value.decode("utf-8")

        # Normalize unicode
        value = unicodedata.normalize("NFKD", value)

        # Replace non-word characters (except . and -)
        value = re.sub(r"[^\w\.-]", self.illegal_character_substitute, value)

        return value.strip().lower()

    def get_component_path(self, component):
        """Get full path for component in location.

        Args:
            component: ftrack Component entity

        Returns:
            Full filesystem path to component
        """
        # Get resource identifier from location structure
        resource_identifier = self.location.structure.get_resource_identifier(
            component
        )

        # Combine with location prefix
        full_path = os.path.join(
            self.location.accessor.prefix,
            os.path.normpath(resource_identifier),
        )

        return str(full_path)

    def resolve_ftrack_path(self, template_path, token_path, entity_creators):
        """Resolve template path using tokens and entity creators.

        Args:
            template_path: Path template with {tokens}
                          e.g. "{ftrack_project_structure}/{ftrack_version}/{ftrack_component}"
            token_path: Path with resolved token values
                       e.g. "Project:MyProj|Shot:sh010/v001/render.####.exr"
            entity_creators: Dict mapping template tokens to creator functions
                            Each function returns a created ftrack entity

        Returns:
            Deepest created entity (typically Component)

        Example:
            >>> entity_creators = {
            ...     "{ftrack_project_structure}": lambda name, parent: create_shot(...),
            ...     "{ftrack_version}": lambda name, parent: create_version(...),
            ...     "{ftrack_component}": lambda name, parent: create_component(...)
            ... }
            >>> component = service.resolve_ftrack_path(
            ...     "{ftrack_project_structure}/{ftrack_version}/{ftrack_component}",
            ...     "Project:MyProj|Shot:sh010/v001/render.exr",
            ...     entity_creators
            ... )
        """
        template_parts = template_path.split(self.path_separator)
        token_parts = token_path.split(self.path_separator)

        if len(template_parts) != len(token_parts):
            raise ValueError(
                f"Template and token paths have different lengths: "
                f"{len(template_parts)} vs {len(token_parts)}"
            )

        parent = None

        # Process each path segment
        for template, token in zip(template_parts, token_parts):
            # Find matching creator function
            creator_fn = entity_creators.get(template)

            if creator_fn:
                # Call creator to build entity
                parent = creator_fn(token, parent)
            else:
                # No creator - just skip this segment
                self.logger.debug(f"Skipping template segment: {template}")

        return parent

    def resolve_project_structure(self, task, template, project_name):
        """Resolve {ftrack_project_structure} token.

        Generates composed name for context hierarchy.

        Args:
            task: Hiero task
            template: Template object with expression
            project_name: ftrack project full name

        Returns:
            Composed name string "Type:Name|Type:Name|..."
            or None if template doesn't match
        """
        from ftrack_nuke_studio.template import match
        import ftrack_nuke_studio.exception
        import hiero.core

        track_item = task._item

        # Build composed name starting with project
        data = [f"Project:{project_name}"]

        # Skip for Sequence items
        if isinstance(track_item, hiero.core.Sequence):
            return self.path_separator.join(data)

        # Match track item against template
        try:
            results = match(track_item, template)
        except ftrack_nuke_studio.exception.TemplateError:
            # Item doesn't match template
            return None

        # Add matched results to composed name
        for result in results:
            sanitised_name = self.sanitise_for_filesystem(result["name"])
            composed_result = f"{result['object_type']}:{sanitised_name}"
            data.append(composed_result)

        return self.path_separator.join(data)

    def resolve_version(self, task, component_registry):
        """Resolve {ftrack_version} token.

        Returns version number based on existing component data.

        Args:
            task: Hiero task
            component_registry: ComponentRegistry instance

        Returns:
            Version string "v001", "v002", etc.
        """
        version = 1  # First version is 1

        # Try to get version from registered component
        try:
            track_name = task._item.parent().name()
            item_name = task._item.name()
            component_name = task.component_name()

            component_data = component_registry.get(
                track_name, item_name, component_name
            )

            if component_data:
                version = component_data["component"]["version"]["version"]

        except (AttributeError, KeyError):
            # Can't get from registry, use default
            pass

        return f"v{version:03d}"

    def resolve_component(self, task, component_pattern):
        """Resolve {ftrack_component} token.

        Generates component filename with pattern.

        Args:
            task: Hiero task
            component_pattern: Pattern like ".{ext}" or ".####.{ext}"

        Returns:
            Component filename
        """
        component_name = self.sanitise_for_filesystem(task._preset.name())
        component_full_name = f"{component_name}{component_pattern}"
        return component_full_name.lower()
