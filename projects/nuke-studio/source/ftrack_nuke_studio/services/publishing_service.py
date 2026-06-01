# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Service for publishing components to ftrack.

This service handles:
- Registering components in ftrack locations
- Generating and uploading thumbnails
- Encoding and uploading reviewable media
- Setting component metadata (frame ranges, fps, handles)
"""

import logging
import tempfile
import clique

try:
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtCore


class PublishingService:
    """Service for publishing components to ftrack.

    Extracted from FtrackProcessor to provide focused publishing operations.
    """

    def __init__(self, session, location):
        """Initialize service with ftrack session and location.

        Args:
            session: ftrack API session
            location: ftrack Location entity for component registration
        """
        self.session = session
        self.location = location
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

    def publish_component(
        self, component, path, start_frame=None, end_frame=None
    ):
        """Register component in ftrack location.

        Args:
            component: ftrack Component entity
            path: Full path to component file/sequence
            start_frame: Start frame for sequences (optional)
            end_frame: End frame for sequences (optional)

        Returns:
            True if published successfully, False otherwise
        """
        self.logger.debug(
            f"Publishing component '{component['name']}' at {path}"
        )

        try:
            # Extract resource identifier (remove location prefix)
            resource_identifier = path.split(self.location.accessor.prefix)[
                -1
            ].lstrip("/\\")

            # Check if component is a container (sequence)
            is_container = "members" in component.keys()

            if (
                is_container
                and start_frame is not None
                and end_frame is not None
            ):
                # Register sequence members
                member_path = (
                    f"{resource_identifier} [{start_frame}-{end_frame}]"
                )
                self.logger.info(f"Registering sequence: {member_path}")

                members = clique.parse(member_path)

                self.location._register_components_in_location(
                    component["members"], members
                )

            # Register main component
            self.location._register_component_in_location(
                component, resource_identifier
            )

            self.logger.info(
                f"Successfully published component '{component['name']}'"
            )

            return True

        except Exception as error:
            self.logger.exception(
                f"Failed to publish component '{component['name']}': {error}"
            )
            return False

    def publish_thumbnail(self, entity, source_item, frame=None):
        """Generate and upload thumbnail for entity.

        Args:
            entity: ftrack entity (AssetVersion, Task, or Shot)
            source_item: Hiero item to extract thumbnail from (TrackItem, Clip, Sequence)
            frame: Frame number to use (defaults to middle frame)

        Returns:
            Path to generated thumbnail file or None if failed
        """
        try:
            # Determine middle frame if not specified
            if frame is None:
                frame = self._get_middle_frame(source_item)

            self.logger.info(
                f"Generating thumbnail at frame {frame} for {entity.entity_type}"
            )

            # Extract thumbnail from Hiero item
            # Layer defaults to "colour" in NS < 16 and "rgb" in NS >= 16
            # Try both for compatibility
            try:
                thumbnail_qimage = source_item.thumbnail(frame, "rgb")
            except RuntimeError:
                thumbnail_qimage = source_item.thumbnail(frame, "colour")

            # Save to temporary file
            thumbnail_file = tempfile.NamedTemporaryFile(
                prefix="ftrack_nuke_thumbnail", suffix=".png", delete=False
            ).name

            # Resize to standard width
            thumbnail_qimage_resized = thumbnail_qimage.scaledToWidth(
                1280, QtCore.Qt.TransformationMode.SmoothTransformation
            )

            thumbnail_qimage_resized.save(thumbnail_file)

            # Upload thumbnail to entity
            if entity.entity_type == "AssetVersion":
                # For version, also upload to task and parent
                entity.create_thumbnail(thumbnail_file)
                if entity.get("task"):
                    entity["task"].create_thumbnail(thumbnail_file)
                    if entity["task"].get("parent"):
                        entity["task"]["parent"].create_thumbnail(
                            thumbnail_file
                        )
            else:
                # For task or shot
                entity.create_thumbnail(thumbnail_file)

            self.logger.info(
                f"Thumbnail uploaded successfully for {entity.entity_type}"
            )

            return thumbnail_file

        except Exception as error:
            self.logger.exception(f"Failed to publish thumbnail: {error}")
            return None

    def publish_reviewable(self, version, media_path):
        """Encode and upload reviewable media.

        Args:
            version: AssetVersion entity
            media_path: Path to media file (typically .mov)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(
                f"Encoding reviewable media for version v{version['version']:03d}"
            )

            version.encode_media(media_path)

            self.logger.info("Reviewable media uploaded successfully")

            return True

        except Exception as error:
            self.logger.exception(f"Failed to publish reviewable: {error}")
            return False

    def set_shot_metadata(
        self, component, start_frame, end_frame, fps, handles
    ):
        """Set frame range and timing metadata on Shot.

        Updates Shot custom attributes with frame information.

        Args:
            component: Component entity (used to find parent Shot)
            start_frame: Start frame number
            end_frame: End frame number
            fps: Frames per second
            handles: Number of handle frames

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get parent shot from component
            parent = component["version"]["task"]["parent"]

            if not parent:
                self.logger.warning("No parent found for component metadata")
                return False

            attributes = parent["custom_attributes"]

            # Update frame range attributes if they exist
            if start_frame is not None and "fstart" in attributes:
                attributes["fstart"] = str(start_frame)
                self.logger.debug(f"Set fstart = {start_frame}")

            if end_frame is not None and "fend" in attributes:
                attributes["fend"] = str(end_frame)
                self.logger.debug(f"Set fend = {end_frame}")

            if fps is not None and "fps" in attributes:
                attributes["fps"] = str(fps)
                self.logger.debug(f"Set fps = {fps}")

            if handles is not None and "handles" in attributes:
                attributes["handles"] = str(handles)
                self.logger.debug(f"Set handles = {handles}")

            self.logger.info(f"Updated metadata for {parent.entity_type}")

            return True

        except Exception as error:
            self.logger.exception(f"Failed to set shot metadata: {error}")
            return False

    def _get_middle_frame(self, source_item):
        """Calculate middle frame for thumbnail.

        Args:
            source_item: Hiero item (TrackItem, Clip, Sequence)

        Returns:
            Middle frame number
        """
        try:
            if hasattr(source_item, "sourceIn") and hasattr(
                source_item, "sourceOut"
            ):
                start = source_item.sourceIn()
                end = source_item.sourceOut()
                return int(((end - start) / 2) + start)
            else:
                # Default to frame 0
                return 0
        except Exception:
            return 0
