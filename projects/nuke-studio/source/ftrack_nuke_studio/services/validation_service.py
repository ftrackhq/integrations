# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Service for export validation.

This service handles:
- Validating task types against schema
- Validating asset types existence
- Checking for duplicate component names
- Validating template matching
"""

import logging


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        """Initialize empty validation result."""
        self.errors = {}  # processor -> {attribute: valid_values}
        self.missing_asset_types = []
        self.duplicate_components = []
        self.non_matching_items = []

    def is_valid(self):
        """Check if validation passed.

        Returns:
            True if no errors, False otherwise
        """
        return not any(
            [
                self.errors,
                self.missing_asset_types,
                self.duplicate_components,
                self.non_matching_items,
            ]
        )

    def __repr__(self):
        return (
            f"ValidationResult("
            f"errors={len(self.errors)}, "
            f"missing_types={len(self.missing_asset_types)}, "
            f"duplicates={len(self.duplicate_components)}, "
            f"non_matching={len(self.non_matching_items)})"
        )


class ValidationService:
    """Service for export validation.

    Extracted from FtrackProcessor to provide focused validation logic.
    """

    def __init__(self, session):
        """Initialize service with ftrack session.

        Args:
            session: ftrack API session
        """
        self.session = session
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

    def validate_processor_settings(
        self, processor, export_items, export_template, project, schema
    ):
        """Validate all processor settings before export.

        Args:
            processor: Processor instance
            export_items: Items to export
            export_template: Export template with tasks
            project: Hiero project
            schema: ftrack ProjectSchema

        Returns:
            ValidationResult with any errors found
        """
        result = ValidationResult()

        self.logger.info("Starting validation...")

        # Validate each export item
        for export_item in export_items:
            item = export_item.item()

            # Skip certain item types
            if self._should_skip_item(item):
                self.logger.debug(f"Skipping {item}")
                continue

            # Validate template match
            if not self._validate_template_match(item, project, result):
                continue

            # Extract task tags
            task_tags = self._extract_task_tags(item)

            # Validate tasks in template
            components = []

            for export_path, preset in export_template.flatten():
                # Create task for validation
                task = self._create_validation_task(
                    preset, item, export_path, export_template
                )

                if not task:
                    continue

                # Check for duplicate components
                component_name = task.component_name()
                if component_name in components:
                    result.duplicate_components.append((component_name, task))
                else:
                    components.append(component_name)

                # Validate asset type
                asset_type_name = preset.properties()["ftrack"][
                    "asset_type_name"
                ]
                self._validate_asset_type(asset_type_name, result)

                # Validate task type
                task_type_name = preset.properties()["ftrack"]["task_type"]
                self._validate_task_type(
                    task_type_name, task_tags, schema, result, processor
                )

        self.logger.info(f"Validation complete: {result}")

        return result

    def validate_asset_type(self, asset_type_name):
        """Check if asset type exists in ftrack.

        Args:
            asset_type_name: Asset type name to check

        Returns:
            AssetType entity or None if not found
        """
        asset_type = self.session.query(
            'AssetType where name is "{0}"'.format(asset_type_name)
        ).first()

        return asset_type

    def validate_task_type(self, project, schema, task_type_name):
        """Check if task type exists in project schema.

        Args:
            project: Project entity
            schema: ProjectSchema entity
            task_type_name: Task type name to check

        Returns:
            TaskType entity

        Raises:
            ValueError: If task type not found in schema
        """
        task_types = schema.get_types("Task")

        filtered_task_types = [
            task_type
            for task_type in task_types
            if task_type["name"] == task_type_name
        ]

        if not filtered_task_types:
            available = [tt["name"] for tt in task_types]
            raise ValueError(
                f"Task type '{task_type_name}' not found in schema. "
                f"Available: {', '.join(available)}"
            )

        return filtered_task_types[0]

    def find_duplicate_components(self, tasks):
        """Check for duplicate component names in tasks.

        Args:
            tasks: List of Hiero tasks

        Returns:
            List of (component_name, task) tuples for duplicates
        """
        seen = {}
        duplicates = []

        for task in tasks:
            component_name = task.component_name()

            if component_name in seen:
                duplicates.append((component_name, task))
            else:
                seen[component_name] = task

        return duplicates

    def validate_template_match(self, item, template):
        """Check if item matches naming template.

        Args:
            item: Hiero item (TrackItem, Sequence, etc)
            template: Template dict with 'expression' key

        Returns:
            True if matches, False otherwise
        """
        from ftrack_nuke_studio.template import match
        import ftrack_nuke_studio.exception

        try:
            match(item, template)
            return True
        except ftrack_nuke_studio.exception.TemplateError:
            return False

    def _should_skip_item(self, item):
        """Check if item should be skipped during validation.

        Args:
            item: Hiero item

        Returns:
            True if should skip, False otherwise
        """
        import hiero.core

        return isinstance(
            item, (hiero.core.EffectTrackItem, hiero.core.Transition)
        )

    def _validate_template_match(self, item, project, result):
        """Validate item against project template.

        Args:
            item: Hiero item
            project: Hiero project
            result: ValidationResult to update

        Returns:
            True if valid, False if doesn't match
        """
        from ftrack_nuke_studio.template import get_project_template

        template = get_project_template(project)

        if not self.validate_template_match(item, template):
            self.logger.warning(
                f"Item '{item.name()}' does not match template: "
                f"{template['expression']}"
            )
            if item.name() not in result.non_matching_items:
                result.non_matching_items.append(item.name())
            return False

        return True

    def _extract_task_tags(self, item):
        """Extract task type names from ftrack tags.

        Args:
            item: Hiero item

        Returns:
            Set of task type names
        """
        task_tags = set()

        if not hasattr(item, "tags"):
            return task_tags

        for tag in item.tags():
            meta = tag.metadata()
            if meta.hasKey("tag.type") and meta.value("tag.type") == "ftrack":
                task_name = meta.value("tag.ftrack_name")
                task_tags.add(task_name)

        return task_tags

    def _create_validation_task(
        self, preset, item, export_path, export_template
    ):
        """Create task for validation purposes.

        Args:
            preset: Task preset
            item: Hiero item
            export_path: Export path template
            export_template: Export template

        Returns:
            Hiero task or None if invalid
        """
        import hiero.core

        try:
            task_data = hiero.core.TaskData(
                preset,
                item,
                preset.properties()["exportRoot"],
                export_path,
                "v0",
                export_template,
                project=item.project(),
                resolver=preset.createResolver(),
            )

            task = hiero.core.taskRegistry.createTaskFromPreset(
                preset, task_data
            )

            return task if task.hasValidItem() else None

        except Exception as error:
            self.logger.warning(f"Failed to create validation task: {error}")
            return None

    def _validate_asset_type(self, asset_type_name, result):
        """Validate asset type and update result.

        Args:
            asset_type_name: Asset type name
            result: ValidationResult to update
        """
        asset_type = self.validate_asset_type(asset_type_name)

        if (
            not asset_type
            and asset_type_name not in result.missing_asset_types
        ):
            result.missing_asset_types.append(asset_type_name)
            self.logger.warning(f"Asset type not found: {asset_type_name}")

    def _validate_task_type(
        self, task_type_name, available_tags, schema, result, processor
    ):
        """Validate task type and update result.

        Args:
            task_type_name: Task type name
            available_tags: Set of task type names from tags
            schema: ProjectSchema
            result: ValidationResult to update
            processor: Processor instance (for error grouping)
        """
        task_types = schema.get_types("Task")

        filtered_task_types = [
            task_type
            for task_type in task_types
            if task_type["name"] == task_type_name
        ]

        if not filtered_task_types:
            # Task type not valid for schema
            preset_errors = result.errors.setdefault(processor, {})
            preset_errors.setdefault("task_type", list(available_tags))

            self.logger.warning(
                f"Task type '{task_type_name}' not valid for schema"
            )
