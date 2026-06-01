# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Service for ftrack entity creation and queries.

This service handles all ftrack entity operations including:
- Creating/querying context entities (Project, Sequence, Shot)
- Creating/querying Assets and AssetVersions
- Creating/querying Components
- Creating/querying Tasks
- Schema queries (task types, statuses, asset types)
"""

import logging


class FtrackEntityService:
    """Service for ftrack entity creation and queries.

    Extracted from FtrackProcessor to provide a focused, testable
    service for entity operations.
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

    def get_or_create_context(self, composed_name, parent, schema):
        """Create context hierarchy (Episodes, Sequences, Shots).

        Args:
            composed_name: Format "TypeA:NameA|TypeB:NameB|..."
                          e.g. "Project:MyProject|Sequence:sq01|Shot:sh010"
            parent: Parent entity or None (for Project)
            schema: Project schema

        Returns:
            Created/existing context entity (deepest in hierarchy)

        Raises:
            ValueError: If composed_name is empty or invalid format

        Example:
            >>> service.get_or_create_context(
            ...     "Sequence:sq01|Shot:sh010",
            ...     parent_project,
            ...     project_schema
            ... )
            <Shot: sh010>
        """
        if not composed_name:
            raise ValueError(f"Empty composed_name provided: {composed_name}")

        self.logger.debug(
            f"Creating context hierarchy: {composed_name} under {parent}"
        )

        # Parse composed name into (type, name) tuples
        splitted_name = composed_name.split("|")
        parsed_names = []

        for raw_name in splitted_name:
            if ":" not in raw_name:
                raise ValueError(
                    f"Invalid format in composed_name: '{raw_name}'. "
                    f"Expected format: 'Type:Name'"
                )

            object_type, object_name = raw_name.split(":", 1)
            parsed_names.append((object_type, object_name))

        # Create hierarchy bottom-up
        current_parent = parent

        for object_type, object_name in parsed_names:
            # Check if entity already exists
            ftrack_entity = self._query_context_entity(
                object_type, object_name, current_parent, schema
            )

            if not ftrack_entity:
                # Create new entity
                ftrack_entity = self._create_context_entity(
                    object_type, object_name, current_parent
                )

                self.logger.info(
                    f"Created {object_type} '{object_name}' under {current_parent}"
                )
            else:
                self.logger.debug(
                    f"Using existing {object_type} '{object_name}'"
                )

            current_parent = ftrack_entity

        return current_parent

    def _query_context_entity(self, object_type, object_name, parent, schema):
        """Query for existing context entity.

        Args:
            object_type: Entity type (Project, Sequence, Shot, etc)
            object_name: Entity name
            parent: Parent entity or None
            schema: Project schema

        Returns:
            Existing entity or None
        """
        query = '{0} where name is "{1}"'

        # Projects use full_name instead of name
        if object_type == "Project":
            query = '{0} where full_name is "{1}"'

        if parent:
            # Has parent - query by parent.id
            query += ' and parent.id is "{2}"'
            result = self.session.query(
                query.format(object_type, object_name, parent["id"])
            ).first()
        else:
            # No parent (Project) - query by schema
            query += ' and project_schema.id is "{2}"'
            result = self.session.query(
                query.format(object_type, object_name, schema["id"])
            ).first()

        return result

    def _create_context_entity(self, object_type, object_name, parent):
        """Create new context entity.

        Args:
            object_type: Entity type
            object_name: Entity name
            parent: Parent entity (required)

        Returns:
            Created entity

        Raises:
            ValueError: If parent is None
        """
        if not parent:
            raise ValueError(
                f"Cannot create {object_type} without parent. "
                f"Projects must already exist."
            )

        self.logger.debug(
            f"Creating {object_type} '{object_name}' under {parent}"
        )

        entity = self.session.create(
            object_type,
            {
                "name": object_name,
                "parent": parent,
            },
        )

        return entity

    def get_or_create_asset(self, name, parent, asset_type):
        """Get or create Asset under parent.

        Args:
            name: Asset name
            parent: Parent entity (Shot, Sequence, etc)
            asset_type: AssetType entity

        Returns:
            Asset entity (existing or newly created)
        """
        self.logger.debug(
            f"Getting/creating asset '{name}' of type {asset_type['name']} "
            f"under {parent}"
        )

        # Query for existing asset
        asset = self.session.query(
            'Asset where name is "{0}" and parent.id is "{1}"'.format(
                name, parent["id"]
            )
        ).first()

        if not asset:
            # Create new asset
            asset = self.session.create(
                "Asset",
                {
                    "name": name,
                    "parent": parent,
                    "type": asset_type,
                },
            )
            self.logger.info(f"Created asset '{name}'")
        else:
            self.logger.debug(f"Using existing asset '{name}'")

        return asset

    def create_version(self, asset, task, status, comment, metadata=None):
        """Create new AssetVersion.

        Args:
            asset: Asset entity
            task: Task entity (optional)
            status: Status entity for AssetVersion
            comment: Version comment/description
            metadata: Optional dict of metadata to set

        Returns:
            Created AssetVersion entity
        """
        self.logger.debug(
            f"Creating version for asset '{asset['name']}' with comment: {comment}"
        )

        version_data = {
            "asset": asset,
            "status": status,
            "comment": comment,
        }

        if task:
            version_data["task"] = task

        version = self.session.create("AssetVersion", version_data)

        # Set metadata if provided
        if metadata:
            for key, value in metadata.items():
                version["metadata"][key] = value

        self.logger.info(
            f"Created version v{version['version']:03d} for asset '{asset['name']}'"
        )

        return version

    def get_or_create_component(
        self,
        version,
        name,
        path_pattern=None,
        start_frame=None,
        end_frame=None,
    ):
        """Get or create Component under version.

        Args:
            version: AssetVersion entity
            name: Component name
            path_pattern: Path pattern for component (optional)
            start_frame: Start frame for sequences (optional)
            end_frame: End frame for sequences (optional)

        Returns:
            Component entity (existing or newly created)
        """
        self.logger.debug(
            f"Getting/creating component '{name}' for version {version['id']}"
        )

        # Check if component already exists
        component = self.session.query(
            'Component where name is "{}" and version.id is "{}"'.format(
                name, version["id"]
            )
        ).first()

        if not component:
            # Determine path pattern
            file_path = name
            if path_pattern:
                file_path = path_pattern

                # Add frame range for sequences
                if start_frame is not None and end_frame is not None:
                    file_path = f"/{path_pattern} [{start_frame}-{end_frame}]"

            # Create component
            component = version.create_component(
                file_path, {"name": name}, location=None
            )

            self.logger.info(
                f"Created component '{name}' with pattern: {file_path}"
            )
        else:
            self.logger.debug(f"Using existing component '{name}'")

        return component

    def get_or_create_task(self, name, parent, task_type, status):
        """Get or create Task under parent.

        Args:
            name: Task name (typically matches task type name)
            parent: Parent entity (Shot, Sequence, etc)
            task_type: TaskType entity
            status: Status entity for Task

        Returns:
            Task entity (existing or newly created)
        """
        self.logger.debug(
            f"Getting/creating task '{name}' of type {task_type['name']} "
            f"under {parent}"
        )

        # Query for existing task
        task = self.session.query(
            'Task where name is "{0}" and parent.id is "{1}"'.format(
                name, parent["id"]
            )
        ).first()

        if not task:
            # Create new task
            task = self.session.create(
                "Task",
                {
                    "name": name,
                    "parent": parent,
                    "status": status,
                    "type": task_type,
                },
            )
            self.logger.info(f"Created task '{name}'")
        else:
            self.logger.debug(f"Using existing task '{name}'")

        return task

    def get_project_schema(self, project):
        """Get project schema.

        Args:
            project: Project entity

        Returns:
            ProjectSchema entity
        """
        query = 'select project_schema from Project where id is "{0}"'.format(
            project["id"]
        )
        project_entity = self.session.query(query).one()
        return project_entity["project_schema"]

    def get_task_type(self, schema, name):
        """Query task type by name from schema.

        Args:
            schema: ProjectSchema entity
            name: Task type name

        Returns:
            TaskType entity

        Raises:
            ValueError: If task type not found in schema
        """
        task_types = schema.get_types("Task")

        filtered_task_types = [
            task_type for task_type in task_types if task_type["name"] == name
        ]

        if not filtered_task_types:
            available = [tt["name"] for tt in task_types]
            raise ValueError(
                f"Task type '{name}' not found in schema. "
                f"Available: {', '.join(available)}"
            )

        return filtered_task_types[0]

    def get_status(self, schema, entity_type, type_id=None):
        """Query status for entity type.

        Args:
            schema: ProjectSchema entity
            entity_type: Entity type name ('Task', 'Shot', 'AssetVersion')
            type_id: Type ID for entity (required for Task)

        Returns:
            First available Status entity

        Raises:
            ValueError: If no statuses found
        """
        if type_id:
            statuses = schema.get_statuses(entity_type, type_id)
        else:
            statuses = schema.get_statuses(entity_type)

        filtered_statuses = [status for status in statuses if status["name"]]

        if not filtered_statuses:
            raise ValueError(f"No statuses found for {entity_type} in schema")

        # Return first status
        return filtered_statuses[0]

    def get_asset_type(self, name):
        """Query AssetType by name.

        Args:
            name: Asset type name

        Returns:
            AssetType entity or None if not found
        """
        result = self.session.query(
            'AssetType where name is "{0}"'.format(name)
        ).first()

        return result

    def create_extra_tasks_from_tags(self, task_type_names, parent, schema):
        """Create extra tasks based on task type names.

        Typically called to create tasks from ftrack tags dropped on items.

        Args:
            task_type_names: List of task type names
            parent: Parent entity (Shot)
            schema: Project schema

        Returns:
            List of created Task entities
        """
        task_types = schema.get_types("Task")
        created_tasks = []

        for task_type_name in task_type_names:
            # Find matching task type
            filtered_task_types = [
                task_type
                for task_type in task_types
                if task_type["name"] == task_type_name
            ]

            if len(filtered_task_types) != 1:
                self.logger.debug(
                    f"Skipping '{task_type_name}' - not a valid task type "
                    f"for schema '{schema['name']}'"
                )
                continue

            task_type = filtered_task_types[0]

            # Get status for this task type
            task_statuses = schema.get_statuses("Task", task_type["id"])

            if not task_statuses:
                self.logger.warning(
                    f"No statuses found for task type '{task_type_name}'"
                )
                continue

            # Create task
            task = self.get_or_create_task(
                task_type_name, parent, task_type, task_statuses[0]
            )

            created_tasks.append(task)

        return created_tasks
