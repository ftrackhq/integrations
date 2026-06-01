# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Core processor logic using composition.

Replaces the inheritance-heavy FtrackProcessor with a lightweight
class that uses composition to access ftrack functionality via the facade.
"""

import logging
from hiero.core.FnExporterBase import TaskCallbacks

from ftrack_nuke_studio.facade import FtrackIntegration
from ftrack_nuke_studio.session import get_shared_session


class FtrackProcessorCore:
    """Core processor that uses composition instead of inheritance.

    This class provides processor-level ftrack functionality by composing
    the FtrackIntegration facade rather than using deep inheritance.

    It handles:
    - Task callbacks (onTaskStart, onTaskFinish)
    - Validation orchestration
    - Project structure creation
    - Path preview updates

    Example:
        >>> class FtrackShotProcessor(ShotProcessor):
        ...     def __init__(self, preset, submission, synchronous=False):
        ...         ShotProcessor.__init__(self, preset, submission, synchronous)
        ...         self.ftrack_core = FtrackProcessorCore(preset)
        ...
        ...     def startProcessing(self, exportItems, preview=False):
        ...         valid = self.ftrack_core.validate_and_create_structure(
        ...             exportItems, self._exportTemplate, self._project, preview
        ...         )
        ...         if valid:
        ...             return ShotProcessor.startProcessing(self, exportItems, preview)
        ...         return False
    """

    def __init__(self, preset):
        """Initialize with preset.

        Args:
            preset: Processor preset with ftrack properties
        """
        self.preset = preset
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

        # Compose ftrack integration facade
        self.ftrack = FtrackIntegration(
            session=get_shared_session(),
            preset_properties=preset.properties().get("ftrack", {}),
        )

        # Setup callbacks for all tasks
        self._setup_callbacks()

        self.logger.info("Initialized FtrackProcessorCore")

    def _setup_callbacks(self):
        """Setup task callbacks for ftrack operations."""
        # Register callbacks if not already registered
        # Note: Callbacks are global, so we need to check if task has _ftrack attribute
        TaskCallbacks.addCallback(
            TaskCallbacks.onTaskStart, self.on_task_start
        )
        TaskCallbacks.addCallback(
            TaskCallbacks.onTaskFinish, self.on_task_finish
        )

        self.logger.debug("Registered task callbacks")

    def on_task_start(self, task):
        """Event handler for task start.

        Called by Hiero when any task starts.
        Only handles tasks with ftrack integration.

        Args:
            task: Hiero task that is starting
        """
        # Only handle tasks with ftrack integration
        if hasattr(task, "_ftrack"):
            self.logger.debug(f"Task starting: {task}")
            task._ftrack.setup_task_paths(task)

    def on_task_finish(self, task):
        """Event handler for task finish.

        Called by Hiero when any task finishes.
        Only handles tasks with ftrack integration.

        Args:
            task: Hiero task that finished
        """
        # Only handle tasks with ftrack integration
        if hasattr(task, "_ftrack"):
            self.logger.debug(f"Task finished: {task}")
            task._ftrack.publish_task_result(task)

    def validate_and_create_structure(
        self, export_items, export_template, project, preview=False
    ):
        """Validate settings and create ftrack structure.

        High-level orchestration method called before export starts.

        Args:
            export_items: Items to export
            export_template: Export template with tasks
            project: Hiero project
            preview: If True, skip validation and structure creation

        Returns:
            Filtered export items if valid, original items if preview,
            empty list if validation failed
        """
        self.logger.info("Starting validation and structure creation")

        if preview:
            self.logger.info("Preview mode - skipping validation")
            return export_items

        # Validate
        result = self.ftrack.validate_export(
            export_items, export_template, project, preview
        )

        if not result.is_valid():
            self.logger.error(f"Validation failed: {result}")
            # Show validation dialog
            self._show_validation_dialog(result)
            return []

        # Propagate properties from processor to tasks
        self._propagate_properties_to_tasks(export_template)

        # Create structure
        filtered_items = self.ftrack.create_project_structure(
            export_items,
            export_template,
            project,
            self.preset.createResolver(),
        )

        self.logger.info(f"Structure created for {len(filtered_items)} items")

        return filtered_items

    def _propagate_properties_to_tasks(self, export_template):
        """Propagate processor properties to all tasks.

        Args:
            export_template: Export template with tasks
        """
        task_type = self.preset.properties()["ftrack"].get("task_type")
        asset_type_name = self.preset.properties()["ftrack"].get(
            "asset_type_name"
        )
        asset_name = self.preset.properties()["ftrack"].get("asset_name")

        for export_path, preset in export_template.flatten():
            if "ftrack" in preset.properties():
                if task_type:
                    preset.properties()["ftrack"]["task_type"] = task_type
                if asset_type_name:
                    preset.properties()["ftrack"]["asset_type_name"] = (
                        asset_type_name
                    )
                if asset_name:
                    preset.properties()["ftrack"]["asset_name"] = asset_name

    def _show_validation_dialog(self, result):
        """Show validation error dialog to user.

        Args:
            result: ValidationResult with errors
        """
        try:
            from PySide2 import QtWidgets
        except ImportError:
            from PySide6 import QtWidgets

        # Build error message
        message_parts = []

        if result.errors:
            message_parts.append(
                f"Invalid settings found in {len(result.errors)} processor(s)"
            )

        if result.missing_asset_types:
            message_parts.append(
                f"Missing asset types: {', '.join(result.missing_asset_types)}"
            )

        if result.duplicate_components:
            dup_names = [name for name, _ in result.duplicate_components]
            message_parts.append(
                f"Duplicate component names: {', '.join(dup_names)}"
            )

        if result.non_matching_items:
            message_parts.append(
                f"Items not matching template: {', '.join(result.non_matching_items)}"
            )

        message = "\n\n".join(message_parts)

        # Show dialog
        dialog = QtWidgets.QMessageBox()
        dialog.setIcon(QtWidgets.QMessageBox.Critical)
        dialog.setWindowTitle("Validation Error")
        dialog.setText("Cannot proceed with export due to validation errors:")
        dialog.setDetailedText(message)
        dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        dialog.exec_()

    def update_path_preview(self, path_preview_widget):
        """Update path preview widget to show ftrack location.

        Args:
            path_preview_widget: QLabel or similar widget to update
        """
        location = self.ftrack.get_location()
        location_name = location["name"]
        mount_point = location.accessor.prefix

        path_preview_widget.setText(
            f"Using Location: {location_name}, with mount point: {mount_point}"
        )

        self.logger.debug(f"Updated path preview: {location_name}")
