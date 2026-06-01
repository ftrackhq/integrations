# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Mixin for ftrack UI functionality.

Provides UI widget creation for ftrack options.
"""

import os
import logging

from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory
from ftrack_nuke_studio.session import get_shared_session


class FtrackUIMixin:
    """Mixin for ftrack UI functionality.

    This mixin provides methods to add ftrack UI widgets to
    Hiero export dialogs.

    Example:
        >>> class FtrackCopyExporterUI(FtrackUIMixin, CopyExporterUI):
        ...     def populateUI(self, widget, exportTemplate):
        ...         CopyExporterUI.populateUI(self, widget, exportTemplate)
        ...         self.add_ftrack_ui_section(widget)

    Usage Pattern:
        1. Mix in FtrackUIMixin before the Hiero UI base class
        2. Call add_ftrack_ui_section() from populateUI()
        3. Optionally call individual widget methods for custom layouts
    """

    def __init__(self):
        """Initialize UI mixin."""
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

    def add_ftrack_ui_section(
        self,
        widget,
        export_items=None,
        include_thumbnail=False,
        include_reviewable=False,
    ):
        """Add ftrack UI section to widget.

        This is the main entry point for adding ftrack UI.
        It creates a "Ftrack Options" section with common widgets.

        Args:
            widget: Parent QWidget
            export_items: Export items (for task type detection)
            include_thumbnail: Whether to add thumbnail option
            include_reviewable: Whether to add reviewable option

        Example:
            >>> def populateUI(self, widget, exportTemplate):
            ...     ParentUI.populateUI(self, widget, exportTemplate)
            ...     self.add_ftrack_ui_section(widget, include_thumbnail=True)
        """
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)

        form_layout.addDivider("Ftrack Options")

        # Add component name widget
        self.add_component_name_widget(form_layout)

        # Add optional thumbnail/reviewable widgets
        if include_thumbnail:
            self.add_thumbnail_option_widget(form_layout)

        if include_reviewable:
            self.add_reviewable_option_widget(form_layout)

        return form_layout

    def add_component_name_widget(self, parent_layout):
        """Add component name input widget.

        Args:
            parent_layout: Parent layout to add widget to
        """
        current_task_name = self._preset.name()

        widget = UIPropertyFactory.create(
            type(current_task_name),
            key="component_name",
            value=current_task_name,
            dictionary=self._preset.properties()["ftrack"],
            label="Component name:",
            tooltip="Name of the component in ftrack",
        )

        parent_layout.addRow("Component name:", widget)

    def add_thumbnail_option_widget(self, parent_layout):
        """Add thumbnail generation option widget.

        Args:
            parent_layout: Parent layout to add widget to
        """
        widget = UIPropertyFactory.create(
            type(True),
            key="opt_publish_thumbnail",
            value=True,
            dictionary=self._preset.properties()["ftrack"],
            label="Publish thumbnail:",
            tooltip="Generate and upload thumbnail to ftrack",
        )

        parent_layout.addRow("Publish thumbnail:", widget)

    def add_reviewable_option_widget(self, parent_layout):
        """Add reviewable media option widget.

        Args:
            parent_layout: Parent layout to add widget to
        """
        widget = UIPropertyFactory.create(
            type(True),
            key="opt_publish_reviewable",
            value=True,
            dictionary=self._preset.properties()["ftrack"],
            label="Publish reviewable:",
            tooltip="Upload media for review in ftrack",
        )

        parent_layout.addRow("Publish reviewable:", widget)

    def add_processor_ui_section(self, widget, export_items):
        """Add processor-level ftrack UI section.

        This adds widgets specific to processors (shot/timeline processors)
        rather than individual tasks.

        Args:
            widget: Parent QWidget
            export_items: Export items

        Returns:
            TaskUIFormLayout with widgets
        """
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)

        form_layout.addDivider("Ftrack Options")

        # Add template selector
        self.add_template_selector_widget(form_layout)

        # Add project display
        self.add_project_display_widget(form_layout)

        # Add task type selector
        if export_items:
            self.add_task_type_selector_widget(form_layout, export_items)

        # Add asset type selector
        self.add_asset_type_selector_widget(form_layout)

        # Add asset name input
        self.add_asset_name_widget(form_layout)

        return form_layout

    def add_template_selector_widget(self, parent_layout):
        """Add shot template selector widget.

        Args:
            parent_layout: Parent layout to add widget to
        """
        from ftrack_nuke_studio.ui.widget.template import Template

        widget = Template(
            self._preset._project
            if hasattr(self._preset, "_project")
            else None
        )
        parent_layout.addRow("Shot template:", widget)

    def add_project_display_widget(self, parent_layout):
        """Add project display widget (read-only).

        Args:
            parent_layout: Parent layout to add widget to
        """
        session = get_shared_session()
        project_id = os.getenv("FTRACK_CONTEXTID")
        project = session.get("Project", project_id)

        widget = UIPropertyFactory.create(
            type(project["full_name"]),
            key="project_name",
            value=project["full_name"],
            dictionary={},
            label="Create under project:",
            tooltip="Current ftrack project",
        )
        widget.setDisabled(True)

        parent_layout.addRow("Create under project:", widget)

    def add_task_type_selector_widget(self, parent_layout, export_items):
        """Add task type selector widget.

        Extracts task types from ftrack tags on items.

        Args:
            parent_layout: Parent layout to add widget to
            export_items: Export items to scan for tags
        """
        from ftrack_nuke_studio.services import TagService

        tag_service = TagService()
        task_tags = tag_service.extract_task_types_from_tags(
            [item.item() for item in export_items]
        )

        task_tags = sorted(list(task_tags)) or [
            self._preset.properties()["ftrack"].get("task_type", "Compositing")
        ]

        widget = UIPropertyFactory.create(
            type(task_tags),
            key="task_type",
            value=task_tags,
            dictionary=self._preset.properties()["ftrack"],
            label="Publish to task:",
            tooltip="Select a task to publish to",
        )
        widget.update(True)

        parent_layout.addRow("Publish to task:", widget)

    def add_asset_type_selector_widget(self, parent_layout):
        """Add asset type selector widget.

        Args:
            parent_layout: Parent layout to add widget to
        """
        session = get_shared_session()
        asset_types = session.query("AssetType").all()
        asset_type_names = [at["name"] for at in asset_types]

        widget = UIPropertyFactory.create(
            type(asset_type_names),
            key="asset_type_name",
            value=asset_type_names,
            dictionary=self._preset.properties()["ftrack"],
            label="Asset type:",
            tooltip="Asset type to be created",
        )
        widget.update(True)

        parent_layout.addRow("Asset type:", widget)

    def add_asset_name_widget(self, parent_layout):
        """Add asset name input widget.

        Args:
            parent_layout: Parent layout to add widget to
        """
        asset_name = self._preset.properties()["ftrack"].get(
            "asset_name", "{track}"
        )

        widget = UIPropertyFactory.create(
            type(asset_name),
            key="asset_name",
            value=asset_name,
            dictionary=self._preset.properties()["ftrack"],
            label="Asset name:",
            tooltip="Asset name pattern (can use tokens like {track}, {shot})",
        )
        widget.update(True)

        parent_layout.addRow("Asset name:", widget)
