# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""
DCC Object Module

This module provides the abstract base class for DCC-specific object tracking
and management within the asset management system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ftrack_framework_asset_manager.asset.constants import *
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)


logger = logging.getLogger(__name__)


class DccObject(dict, ABC):
    """
    Abstract base class for DCC-specific object representation.

    This class serves as a base for DCC-specific implementations that handle
    the creation and management of objects within specific DCC applications.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the DCC object with provided data."""
        super().__init__(*args, **kwargs)

        # Ensure required keys are present
        if DCC_OBJECT_NAME not in self:
            self[DCC_OBJECT_NAME] = None

        if OBJECTS_LOADED not in self:
            self[OBJECTS_LOADED] = False

    @classmethod
    @abstractmethod
    def create(
        cls,
        asset_info: FtrackAssetInfo,
        options: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "DccObject":
        """
        Create a new DCC object from asset information.

        Args:
            asset_info: The FtrackAssetInfo instance
            options: Additional options for object creation
            **kwargs: Additional keyword arguments

        Returns:
            DccObject instance

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def _name_exists(self, name: str) -> bool:
        """
        Check if a DCC object with the given name already exists.

        Args:
            name: The name to check

        Returns:
            bool: True if the object exists, False otherwise

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def from_asset_info_id(
        cls, asset_info_id: str, **kwargs: Any
    ) -> Optional["DccObject"]:
        """
        Get a DCC object from an asset info ID.

        Args:
            asset_info_id: The asset info ID to look up
            **kwargs: Additional keyword arguments

        Returns:
            DccObject instance or None if not found

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def dictionary_from_object(self) -> Dict[str, Any]:
        """
        Get a dictionary representation of the DCC object.

        Returns:
            Dictionary representation of the object

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def connect_objects(self, *args: Any, **kwargs: Any) -> None:
        """
        Connect this DCC object with other objects.

        Args:
            *args: Positional arguments for connection
            **kwargs: Keyword arguments for connection

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
        """
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def objects_loaded(self) -> bool:
        """
        Get whether objects have been loaded.

        Returns:
            bool: True if objects are loaded, False otherwise
        """
        return bool(self.get(OBJECTS_LOADED, False))

    @objects_loaded.setter
    def objects_loaded(self, value: bool) -> None:
        """
        Set whether objects have been loaded.

        Args:
            value: Boolean value to set
        """
        self[OBJECTS_LOADED] = bool(value)

    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to dictionary keys."""
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow attribute-style assignment to dictionary keys."""
        self[name] = value
