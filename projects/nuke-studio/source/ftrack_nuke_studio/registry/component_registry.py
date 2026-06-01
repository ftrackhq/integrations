# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Thread-safe registry for component metadata during export.

Replaces the problematic class variable _components = {} in FtrackBase
which caused state pollution between processor instances.
"""

import threading
import logging


class ComponentRegistry:
    """Thread-safe registry for component metadata during export.

    This registry manages component data during the export process,
    storing information needed for publishing components after tasks finish.

    Each component is identified by:
    - track_name: Name of Hiero track
    - item_name: Name of Hiero item (TrackItem, Clip, etc)
    - component_name: Name of component being exported

    Component data includes:
    - component: ftrack Component entity
    - path: Full filesystem path to component
    - published: Whether component has been published to ftrack

    Example:
        >>> registry = ComponentRegistry()
        >>> registry.register('Video', 'sh010', 'render', {
        ...     'component': component_entity,
        ...     'path': '/path/to/render.exr',
        ...     'published': False
        ... })
        >>> data = registry.get('Video', 'sh010', 'render')
        >>> registry.update_published_status('Video', 'sh010', 'render')
    """

    def __init__(self):
        """Initialize empty registry with thread safety."""
        self._registry = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

    def register(self, track_name, item_name, component_name, data):
        """Register component data.

        Args:
            track_name: Name of Hiero track
            item_name: Name of Hiero item
            component_name: Name of component
            data: Dict with keys:
                - component: ftrack Component entity
                - path: Full filesystem path
                - published: Whether published (default False)

        Raises:
            ValueError: If data missing required keys
        """
        # Validate data
        required_keys = ["component", "path"]
        missing = [k for k in required_keys if k not in data]
        if missing:
            raise ValueError(f"Missing required keys in data: {missing}")

        # Ensure published flag exists
        if "published" not in data:
            data["published"] = False

        with self._lock:
            # Create nested structure
            self._registry.setdefault(track_name, {})
            self._registry[track_name].setdefault(item_name, {})

            # Store data
            self._registry[track_name][item_name][component_name] = data

            self.logger.debug(
                f"Registered: {track_name}/{item_name}/{component_name}"
            )

    def get(self, track_name, item_name, component_name):
        """Retrieve component data.

        Args:
            track_name: Name of Hiero track
            item_name: Name of Hiero item
            component_name: Name of component

        Returns:
            Component data dict or None if not found
        """
        with self._lock:
            return (
                self._registry.get(track_name, {})
                .get(item_name, {})
                .get(component_name)
            )

    def has_data(self, track_name, item_name, component_name):
        """Check if data exists for component.

        Args:
            track_name: Name of Hiero track
            item_name: Name of Hiero item
            component_name: Name of component

        Returns:
            True if data exists, False otherwise
        """
        return self.get(track_name, item_name, component_name) is not None

    def update_published_status(self, track_name, item_name, component_name):
        """Mark component as published.

        Args:
            track_name: Name of Hiero track
            item_name: Name of Hiero item
            component_name: Name of component

        Returns:
            True if updated, False if component not found
        """
        data = self.get(track_name, item_name, component_name)

        if data:
            with self._lock:
                data["published"] = True
                self.logger.debug(
                    f"Marked as published: {track_name}/{item_name}/{component_name}"
                )
            return True

        return False

    def clear(self):
        """Clear all registered data.

        Typically called at the start of a new export to ensure clean state.
        """
        with self._lock:
            self._registry.clear()
            self.logger.debug("Registry cleared")

    def get_all_for_item(self, track_name, item_name):
        """Get all components for an item.

        Args:
            track_name: Name of Hiero track
            item_name: Name of Hiero item

        Returns:
            Dict of {component_name: data} or empty dict if not found
        """
        with self._lock:
            return (
                self._registry.get(track_name, {})
                .get(item_name, {})
                .copy()  # Return copy to avoid external modification
            )

    def get_all_for_track(self, track_name):
        """Get all items and components for a track.

        Args:
            track_name: Name of Hiero track

        Returns:
            Dict of {item_name: {component_name: data}} or empty dict if not found
        """
        with self._lock:
            track_data = self._registry.get(track_name, {})
            # Return deep copy
            return {
                item_name: components.copy()
                for item_name, components in track_data.items()
            }

    def get_unpublished_components(self):
        """Get all components that haven't been published yet.

        Returns:
            List of tuples: (track_name, item_name, component_name, data)
        """
        unpublished = []

        with self._lock:
            for track_name, track_data in self._registry.items():
                for item_name, item_data in track_data.items():
                    for component_name, data in item_data.items():
                        if not data.get("published", False):
                            unpublished.append(
                                (track_name, item_name, component_name, data)
                            )

        return unpublished

    def get_statistics(self):
        """Get registry statistics.

        Returns:
            Dict with statistics:
            - total_tracks: Number of tracks
            - total_items: Number of items across all tracks
            - total_components: Number of components across all items
            - published_components: Number of published components
            - unpublished_components: Number of unpublished components
        """
        with self._lock:
            stats = {
                "total_tracks": len(self._registry),
                "total_items": 0,
                "total_components": 0,
                "published_components": 0,
                "unpublished_components": 0,
            }

            for track_data in self._registry.values():
                stats["total_items"] += len(track_data)

                for item_data in track_data.values():
                    stats["total_components"] += len(item_data)

                    for data in item_data.values():
                        if data.get("published", False):
                            stats["published_components"] += 1
                        else:
                            stats["unpublished_components"] += 1

            return stats

    def __repr__(self):
        """String representation showing statistics."""
        stats = self.get_statistics()
        return (
            f"ComponentRegistry("
            f"tracks={stats['total_tracks']}, "
            f"items={stats['total_items']}, "
            f"components={stats['total_components']}, "
            f"published={stats['published_components']})"
        )
