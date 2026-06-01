# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Service for Hiero tag management.

This service handles:
- Creating and updating ftrack tags on Hiero items
- Storing component metadata in tags
- Extracting task information from tags
"""

import time
import logging
import hiero.core


class TagService:
    """Service for Hiero tag management.

    Extracted from FtrackProcessor to provide focused tag operations.
    """

    def __init__(self):
        """Initialize tag service."""
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

    def create_or_update_ftrack_tag(self, item, component, task_data):
        """Create or update ftrack tag on Hiero item.

        Args:
            item: Hiero TrackItem
            component: ftrack Component entity
            task_data: Dict with task metadata:
                - task_id: Preset task ID
                - task_name: Component name
                - path: ftrack path
                - path_template: Export path template
                - start_frame: Start frame
                - end_frame: End frame
                - start_handle: Start handle frames
                - end_handle: End handle frames
                - frame_offset: Frame offset
                - cut_handles: Cut handles
                - applying_retime: Whether retimes applied
                - script_path: Nuke script path (optional)
                - source_retime: Source retime value (optional)
        """
        if not self._can_use_tags(item):
            self.logger.debug(f"Cannot use tags on {item}")
            return

        self.logger.info(f"Creating/updating ftrack tag on {item}")

        task_id = str(task_data["task_id"])
        task_name = task_data["task_name"]

        # Check if tag already exists
        existing_tag = self._find_existing_tag(item, task_id, task_name)

        if existing_tag:
            # Update existing tag
            self._update_tag_metadata(existing_tag, component, task_data)
            item.removeTag(existing_tag)
            item.addTag(existing_tag)
        else:
            # Create new tag
            tag = self._create_new_tag(task_name, component, task_data)
            item.addTag(tag)

    def get_ftrack_tags(self, item):
        """Get all ftrack tags from Hiero item.

        Args:
            item: Hiero item

        Returns:
            List of ftrack Tag objects
        """
        if not hasattr(item, "tags"):
            return []

        ftrack_tags = []

        for tag in item.tags():
            meta = tag.metadata()
            if (
                meta.hasKey("tag.provider")
                and meta.value("tag.provider") == "ftrack"
            ):
                ftrack_tags.append(tag)

        return ftrack_tags

    def extract_task_types_from_tags(self, items):
        """Extract task type names from ftrack tags.

        Args:
            items: List of Hiero items

        Returns:
            Set of task type names
        """
        task_types = set()

        for item in items:
            if not hasattr(item, "tags"):
                continue

            for tag in item.tags():
                meta = tag.metadata()
                if (
                    meta.hasKey("tag.type")
                    and meta.value("tag.type") == "ftrack"
                ):
                    task_name = meta.value("tag.ftrack_name")
                    task_types.add(task_name)

        return task_types

    def _can_use_tags(self, item):
        """Check if item supports tags.

        Args:
            item: Hiero item

        Returns:
            True if item can have tags, False otherwise
        """
        return all(
            [
                hasattr(item, "tags"),
                hasattr(item, "sourceIn"),
                hasattr(item, "sourceOut"),
                not isinstance(item, hiero.core.Sequence),
            ]
        )

    def _find_existing_tag(self, item, task_id, task_name):
        """Find existing ftrack tag for task.

        Args:
            item: Hiero item
            task_id: Preset task ID
            task_name: Component name

        Returns:
            Existing Tag or None
        """
        for tag in item.tags():
            meta = tag.metadata()
            if (
                meta.hasKey("tag.presetid")
                and meta["tag.presetid"] == task_id
                and meta.hasKey("tag.task_name")
                and meta["tag.task_name"] == task_name
            ):
                return tag

        return None

    def _create_new_tag(self, task_name, component, task_data):
        """Create new ftrack tag.

        Args:
            task_name: Component name
            component: ftrack Component entity
            task_data: Task metadata dict

        Returns:
            New Tag object
        """
        tag = hiero.core.Tag(
            f"{task_name}",
            ":/ftrack/image/default/ftrackLogoColor",
            False,
        )

        # Set metadata
        self._update_tag_metadata(tag, component, task_data)

        tag.metadata().setValue("tag.provider", "ftrack")
        tag.metadata().setValue("tag.task_name", task_name)
        tag.metadata().setValue("tag.description", f"ftrack {task_name}")

        return tag

    def _update_tag_metadata(self, tag, component, task_data):
        """Update tag metadata.

        Args:
            tag: Hiero Tag object
            component: ftrack Component entity
            task_data: Task metadata dict
        """
        meta = tag.metadata()

        # ftrack IDs
        meta.setValue("tag.presetid", task_data["task_id"])
        meta.setValue("tag.component_id", component["id"])
        meta.setValue("tag.version_id", component["version"]["id"])
        meta.setValue("tag.asset_id", component["version"]["asset"]["id"])
        meta.setValue("tag.version", str(component["version"]["version"]))

        # Paths
        meta.setValue("tag.path", task_data["path"])
        meta.setValue("tag.pathtemplate", task_data["path_template"])

        # Frame info
        start = task_data["start_frame"]
        end = task_data["end_frame"]
        meta.setValue("tag.startframe", str(start))
        meta.setValue("tag.duration", str(end - start + 1))
        meta.setValue("tag.starthandle", str(task_data["start_handle"]))
        meta.setValue("tag.endhandle", str(task_data["end_handle"]))
        meta.setValue("tag.frameoffset", str(task_data["frame_offset"]))

        # Timestamp
        localtime = time.localtime(time.time())
        meta.setValue("tag.localtime", str(localtime))

        # Retimes
        applying_retime = task_data.get("applying_retime", False)
        meta.setValue("tag.appliedretimes", "1" if applying_retime else "0")

        # Optional fields
        if task_data.get("script_path"):
            meta.setValue("tag.script", task_data["script_path"])

        if task_data.get("cut_handles"):
            meta.setValue("tag.handles", str(task_data["cut_handles"]))

        if task_data.get("source_retime"):
            meta.setValue("tag.sourceretime", str(task_data["source_retime"]))
