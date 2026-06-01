# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""ftrack integration facade.

This facade composes all services and provides a single entry point
for all ftrack operations. It orchestrates the services to provide
high-level functionality for processors and tasks.
"""

import os
import logging
import hiero.core

from ftrack_nuke_studio.services import (
    FtrackEntityService,
    PublishingService,
    PathResolutionService,
    ValidationService,
    TagService,
)
from ftrack_nuke_studio.registry import ComponentRegistry
from ftrack_nuke_studio.exception import FtrackLocationError


class FtrackIntegration:
    """Facade for ftrack operations, composing all services.

    This is the single entry point for all ftrack functionality.
    It composes all services and provides high-level orchestration.

    Example:
        >>> integration = FtrackIntegration(session, preset_properties)
        >>> result = integration.validate_export(export_items, export_template)
        >>> if result.is_valid():
        ...     integration.create_project_structure(export_items, export_template, project)
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

    def __init__(self, session, preset_properties):
        """Initialize facade with ftrack session and preset properties.

        Args:
            session: ftrack API session
            preset_properties: Dict with ftrack-specific properties

        Raises:
            FtrackLocationError: If location is invalid
        """
        self.session = session
        self.properties = preset_properties
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

        # Get and validate ftrack location
        self._location = session.pick_location()
        self._validate_location()

        # Compose all services
        self.entity_service = FtrackEntityService(session)
        self.publishing_service = PublishingService(session, self._location)
        self.path_service = PathResolutionService(self._location)
        self.validation_service = ValidationService(session)
        self.tag_service = TagService()
        self.registry = ComponentRegistry()

        self.logger.info(
            f"Initialized with location: {self._location['name']}"
        )

    def _validate_location(self):
        """Validate that location is usable.

        Raises:
            FtrackLocationError: If location is in ignored list
        """
        location_name = self._location["name"]

        if location_name in self.IGNORED_LOCATIONS:
            raise FtrackLocationError(
                location_name,
                reason="This location is not valid for Nuke Studio. "
                "Please setup a centralized storage scenario or custom location.",
            )

    def get_location(self):
        """Get ftrack location.

        Returns:
            ftrack Location entity
        """
        return self._location

    def validate_export(
        self, export_items, export_template, project, preview=False
    ):
        """High-level validation method.

        Args:
            export_items: Items to export
            export_template: Export template
            project: Hiero project
            preview: If True, skip validation

        Returns:
            ValidationResult
        """
        if preview:
            from ftrack_nuke_studio.services.validation_service import (
                ValidationResult,
            )

            return ValidationResult()  # Empty, valid result

        self.logger.info("Validating export settings...")

        # Get project schema
        project_id = os.getenv("FTRACK_CONTEXTID")
        ftrack_project = self.session.get("Project", project_id)
        schema = self.entity_service.get_project_schema(ftrack_project)

        # Run validation
        result = self.validation_service.validate_processor_settings(
            self, export_items, export_template, project, schema
        )

        if not result.is_valid():
            self.logger.warning(f"Validation failed: {result}")

        return result

    def create_project_structure(
        self, export_items, export_template, project, resolver
    ):
        """High-level method to create entire project structure.

        Args:
            export_items: Items to export
            export_template: Export template with tasks
            project: Hiero project
            resolver: Token resolver for path resolution

        Returns:
            Filtered list of export items (items that matched template)
        """
        self.logger.info("Creating project structure in ftrack...")

        filtered_items = []
        self.registry.clear()  # Start fresh

        # Get ftrack project
        project_id = os.getenv("FTRACK_CONTEXTID")
        ftrack_project = self.session.get("Project", project_id)
        schema = self.entity_service.get_project_schema(ftrack_project)

        # Get project template for validation
        from ftrack_nuke_studio.template import get_project_template

        parsing_template = get_project_template(project)

        num_items = len(self._flatten_template(export_template)) * len(
            export_items
        )
        progress_index = 0

        for export_item in export_items:
            track_item = export_item.item()

            # Skip certain item types
            if self._should_skip_item(track_item):
                self.logger.debug(f"Skipping {track_item}")
                continue

            # Validate template match
            if not self._validate_template_for_item(
                track_item, parsing_template
            ):
                self.logger.warning(
                    f"Item {track_item.name()} doesn't match template"
                )
                continue

            # Process each task in template
            for export_path, preset in self._flatten_template(export_template):
                progress_index += 1
                self.logger.debug(
                    f"Processing {progress_index}/{num_items}: {track_item.name()}"
                )

                # Collect task tags
                task_tags = self.tag_service.extract_task_types_from_tags(
                    [track_item]
                )

                # Create task
                task = self._create_hiero_task(
                    preset,
                    track_item,
                    export_path,
                    export_template,
                    project,
                    resolver,
                )

                if not task or not task.hasValidItem():
                    continue

                # Check if task is disabled
                if getattr(task, "_nothingToDo", False):
                    self.logger.warning(f"Task {task} is disabled, skipping")
                    continue

                # Add to filtered items
                if export_item not in filtered_items:
                    filtered_items.append(export_item)

                # Create ftrack structure for this task
                component = self._create_ftrack_structure_for_task(
                    task, track_item, export_path, ftrack_project, schema
                )

                if not component:
                    continue

                # Create extra tasks from tags
                if task_tags:
                    self.entity_service.create_extra_tasks_from_tags(
                        task_tags,
                        component["version"]["asset"]["parent"],
                        schema,
                    )
                    self.session.commit()

                # Register component
                self._register_component_for_task(task, track_item, component)

                # Add tag to Hiero item
                self._add_tag_to_item(track_item, component, task)

        self.logger.info(
            f"Created structure for {len(filtered_items)} items. "
            f"Registry: {self.registry}"
        )

        return filtered_items

    def setup_task_paths(self, task):
        """Configure paths for a task before execution.

        Called by onTaskStart callback.

        Args:
            task: Hiero task about to start
        """
        # Get registered component data
        track_name, item_name = self._get_task_identifiers(task)
        component_data = self.registry.get(
            track_name, item_name, task.component_name()
        )

        if not component_data:
            self.logger.debug(
                f"No component data for {track_name}/{item_name}/{task.component_name()}"
            )
            return

        # Override task path with ftrack path
        ftrack_path = component_data["path"]
        task._exportPath = ftrack_path
        task.setDestinationDescription(ftrack_path)

        # Create directories if needed
        base_path = os.path.dirname(ftrack_path)
        if not os.path.exists(base_path):
            self.logger.debug(f"Creating directory: {base_path}")
            os.makedirs(base_path)

        # Disable Hiero's path creation
        task._makePath = lambda: None

        self.logger.info(f"Setup paths for task: {ftrack_path}")

    def publish_task_result(self, task):
        """Publish task results after execution.

        Called by onTaskFinish callback.

        Args:
            task: Hiero task that finished
        """
        if not task._item:
            return

        if task.error():
            self.logger.warning(
                f"Task error, skipping publish: {task.error()}"
            )
            return

        # Get component data
        track_name, item_name = self._get_task_identifiers(task)
        component_data = self.registry.get(
            track_name, item_name, task.component_name()
        )

        if not component_data:
            self.logger.debug("No component data, skipping publish")
            return

        if component_data["published"]:
            self.logger.debug("Already published, skipping")
            return

        component = component_data["component"]
        path = component_data["path"]

        self.logger.info(
            f"Publishing component '{component['name']}' at {path}"
        )

        # Get frame range
        start, end = self._get_frame_range(task)

        # Publish component
        success = self.publishing_service.publish_component(
            component, path, start, end
        )

        if not success:
            self.logger.error("Failed to publish component")
            return

        # Publish optional thumbnail
        if self.properties.get("opt_publish_thumbnail"):
            self.publishing_service.publish_thumbnail(
                component["version"], task._item
            )

        # Publish optional reviewable
        if self.properties.get("opt_publish_reviewable"):
            if path.endswith(".mov"):
                self.publishing_service.publish_reviewable(
                    component["version"], path
                )

        # Update shot metadata
        start_handle, end_handle = task.outputHandles()
        fps = self._get_fps(task)

        self.publishing_service.set_shot_metadata(
            component, start, end, fps, start_handle
        )

        # Commit and mark as published
        self.session.commit()
        self.registry.update_published_status(
            track_name, item_name, task.component_name()
        )

        self.logger.info("Publishing complete")

    # Private helper methods

    def _should_skip_item(self, item):
        """Check if item should be skipped."""
        return isinstance(
            item, (hiero.core.EffectTrackItem, hiero.core.Transition)
        )

    def _validate_template_for_item(self, item, template):
        """Validate item against template."""
        return self.validation_service.validate_template_match(item, template)

    def _flatten_template(self, export_template):
        """Flatten export template to list of (path, preset) tuples."""
        return export_template.flatten()

    def _create_hiero_task(
        self, preset, item, export_path, export_template, project, resolver
    ):
        """Create Hiero task for export."""
        from hiero.exporters.FnShotProcessor import getShotNameIndex

        shot_name_index = getShotNameIndex(item)

        try:
            task_data = hiero.core.TaskData(
                preset,
                item,
                preset.properties()["exportRoot"],
                export_path,
                "v0",
                export_template,
                project=project,
                resolver=resolver,
                shotNameIndex=shot_name_index,
            )

            task = hiero.core.taskRegistry.createTaskFromPreset(
                preset, task_data
            )

            return task

        except Exception as error:
            self.logger.exception(f"Failed to create task: {error}")
            return None

    def _create_ftrack_structure_for_task(
        self, task, track_item, export_path, ftrack_project, schema
    ):
        """Create ftrack entity structure for task.

        Returns:
            Component entity or None
        """
        try:
            # Build path tokens
            template_parts = export_path.split(
                self.path_service.path_separator
            )

            # Create entity creators mapping
            entity_creators = {
                "{ftrack_project_structure}": lambda token,
                parent: self._create_context_fragment(
                    token, parent, task, ftrack_project, schema
                ),
                "{ftrack_version}": lambda token,
                parent: self._create_version_fragment(
                    token, parent, task, ftrack_project, schema
                ),
                "{ftrack_component}": lambda token,
                parent: self._create_component_fragment(token, parent, task),
            }

            # Resolve path to create entities
            path = task.resolvePath(export_path)
            token_parts = path.split(self.path_service.path_separator)

            parent = None
            for template, token in zip(template_parts, token_parts):
                creator_fn = entity_creators.get(template)
                if creator_fn:
                    parent = creator_fn(token, parent)

            # Commit entities
            self.session.commit()

            return parent  # Final parent is the component

        except Exception as error:
            self.logger.exception(
                f"Failed to create ftrack structure: {error}"
            )
            return None

    def _create_context_fragment(
        self, composed_name, parent, task, ftrack_project, schema
    ):
        """Create context entities (Project/Sequence/Shot)."""
        from ftrack_nuke_studio.template import get_project_template

        template = get_project_template(task._project)

        # Resolve project structure
        project_structure = self.path_service.resolve_project_structure(
            task, template, ftrack_project["full_name"]
        )

        if not project_structure:
            return None

        # Create context hierarchy
        context = self.entity_service.get_or_create_context(
            project_structure, None, schema
        )

        return context

    def _create_version_fragment(
        self, name, parent, task, ftrack_project, schema
    ):
        """Create asset and version entities."""
        # Get asset name from preset
        asset_name_pattern = self.properties["asset_name"]
        resolved_asset_name = task._resolver.resolve(task, asset_name_pattern)
        asset_name = self.path_service.sanitise_for_filesystem(
            resolved_asset_name
        )

        # Get or create asset
        asset_type_name = task._preset.properties()["ftrack"][
            "asset_type_name"
        ]
        asset_type = self.entity_service.get_asset_type(asset_type_name)

        asset = self.entity_service.get_or_create_asset(
            asset_name, parent, asset_type
        )

        # Get or create task
        task_type_name = self.properties["task_type"]
        task_type = self.entity_service.get_task_type(schema, task_type_name)
        task_status = self.entity_service.get_status(
            schema, "Task", task_type["id"]
        )

        ftask = self.entity_service.get_or_create_task(
            task_type_name, asset["parent"], task_type, task_status
        )

        # Create version
        version_status = self.entity_service.get_status(schema, "AssetVersion")
        comment = f"Publish {asset_type['name']} to {parent['name']}"

        # Get Hiero version tuple
        from ftrack_nuke_studio.base import FtrackBase

        base = FtrackBase()
        hiero_version_tuple = base.hiero_version_tuple

        metadata = {
            "app_metadata": f"Published with Nuke Studio {'.'.join(map(str, hiero_version_tuple))}"
        }

        version = self.entity_service.create_version(
            asset, ftask, version_status, comment, metadata
        )

        return version

    def _create_component_fragment(self, name, parent, task):
        """Create component entity."""
        import re

        component_name = task.component_name()

        # Check if sequence
        is_sequence = re.search(
            r"(?<=\.)((%+\d+d)|(#+)|(%d)|(\d+))(?=\.)", name
        )

        start_frame, end_frame = None, None
        if is_sequence:
            start_frame, end_frame = self._get_frame_range(task)

        component = self.entity_service.get_or_create_component(
            parent, component_name, name, start_frame, end_frame
        )

        return component

    def _register_component_for_task(self, task, track_item, component):
        """Register component in registry."""
        try:
            root_item = track_item.parentTrack().name()
        except (AttributeError, RuntimeError):
            root_item = track_item.name()

        # Get ftrack path
        ftrack_path = self.path_service.get_component_path(component)

        data = {
            "component": component,
            "path": ftrack_path,
            "published": False,
        }

        self.registry.register(
            root_item, track_item.name(), task.component_name(), data
        )

    def _add_tag_to_item(self, track_item, component, task):
        """Add ftrack tag to Hiero item."""
        start, end = self._get_frame_range(task)
        start_handle, end_handle = task.outputHandles()

        frame_offset = start if start else 0

        # Check if applying retimes
        collate = getattr(task, "_collate", False)
        applying_retime = (
            task._retime and task._cutHandles is not None
        ) or collate

        # Build task data
        task_data = {
            "task_id": str(task._preset.properties()["ftrack"]["task_id"]),
            "task_name": task.component_name(),
            "path": self.registry.get(
                track_item.parentTrack().name()
                if hasattr(track_item, "parentTrack")
                else track_item.name(),
                track_item.name(),
                task.component_name(),
            )["path"],
            "path_template": task._exportPath,
            "start_frame": start,
            "end_frame": end,
            "start_handle": start_handle,
            "end_handle": end_handle,
            "frame_offset": frame_offset,
            "cut_handles": task._cutHandles
            if hasattr(task, "_cutHandles")
            else None,
            "applying_retime": applying_retime,
            "script_path": task.resolvedExportPath()
            if task._preset.properties().get("keepNukeScript")
            else None,
            "source_retime": track_item.playbackSpeed()
            if isinstance(track_item, hiero.core.TrackItem)
            else None,
        }

        self.tag_service.create_or_update_ftrack_tag(
            track_item, component, task_data
        )

    def _get_task_identifiers(self, task):
        """Get track and item names from task."""
        try:
            track_name = task._item.parentTrack().name()
        except (AttributeError, RuntimeError):
            track_name = task._item.name()

        item_name = task._item.name()

        return track_name, item_name

    def _get_frame_range(self, task):
        """Get start and end frames from task."""
        start, end = task.outputRange(clampToSource=False)
        return start, end

    def _get_fps(self, task):
        """Get FPS from task."""
        if task._sequence:
            return task._sequence.framerate().toFloat()
        elif task._clip:
            return task._clip.framerate().toFloat()
        return None
