# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""
Ftrack Object Manager Module

This module provides the FtrackObjectManager class which manages synchronization
between FtrackAssetInfo and DCC objects.
"""

import logging
import re
from typing import Any, Dict, Optional, Type, Union

from ftrack_framework_asset_manager.asset.constants import *
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)
from ftrack_framework_asset_manager.asset.dcc_object import DccObject


logger = logging.getLogger(__name__)


class FtrackObjectManager:
    """
    Manager class for synchronizing between FtrackAssetInfo and DCC objects.

    This class handles the creation, synchronization, and connection of DCC objects
    with their corresponding asset information.
    """

    def __init__(
        self,
        asset_info: FtrackAssetInfo,
        dcc_object: Optional[DccObject] = None,
        session: Optional[Any] = None,
        event_manager: Optional[Any] = None,
    ) -> None:
        """
        Initialize the object manager.

        Args:
            asset_info: The FtrackAssetInfo instance
            dcc_object: Optional DCC object instance
            session: ftrack_api session object
            event_manager: Optional event manager instance
        """
        self._asset_info = asset_info
        self._dcc_object = dcc_object
        self._session = session
        self._event_manager = event_manager

        # Set up logging for this instance
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    @property
    def asset_info(self) -> FtrackAssetInfo:
        """Get the asset info instance."""
        return self._asset_info

    @property
    def dcc_object(self) -> Optional[DccObject]:
        """Get the DCC object instance."""
        return self._dcc_object

    @property
    def session(self) -> Optional[Any]:
        """Get the ftrack session."""
        return self._session

    @property
    def event_manager(self) -> Optional[Any]:
        """Get the event manager."""
        return self._event_manager

    @property
    def is_sync(self) -> bool:
        """Check if asset info and DCC object are in sync."""
        return self._check_sync()

    @property
    def objects_loaded(self) -> bool:
        """Check if objects have been loaded."""
        return self._dcc_object.objects_loaded if self._dcc_object else False

    def generate_dcc_object_name(self) -> str:
        """
        Generate a name for the DCC object based on asset information.

        Uses regex patterns to clean asset and component names by:
        1. Removing special characters (keeping only word chars, spaces, hyphens)
        2. Replacing spaces and hyphens with underscores
        3. Building a structured name: asset_vVersion_component or asset_vVersion

        Returns:
            Generated DCC object name
        """
        asset_name = self._asset_info.get(ASSET_NAME, "")
        version_number = self._asset_info.get(VERSION_NUMBER, "")
        component_name = self._asset_info.get(COMPONENT_NAME, "")

        # Clean names using regex: remove special chars, normalize whitespace
        clean_asset_name = re.sub(r'[^\w\s-]', '', asset_name).strip()
        clean_asset_name = re.sub(r'[\s-]+', '_', clean_asset_name)

        clean_component_name = re.sub(r'[^\w\s-]', '', component_name).strip()
        clean_component_name = re.sub(r'[\s-]+', '_', clean_component_name)

        # Build structured name with fallback
        if clean_component_name:
            name = (
                f"{clean_asset_name}_v{version_number}_{clean_component_name}"
            )
        else:
            name = f"{clean_asset_name}_v{version_number}"

        return name or "ftrack_asset"

    def _check_sync(self) -> bool:
        """
        Check if the asset info and DCC object are in sync.

        Returns:
            True if in sync, False otherwise
        """
        if not self._dcc_object:
            return False

        # Check if asset info ID matches
        asset_info_id = self._asset_info.get(ASSET_INFO_ID)
        dcc_asset_info_id = self._dcc_object.get(ASSET_INFO_ID)

        if asset_info_id != dcc_asset_info_id:
            return False

        # Check if dependency IDs match
        asset_dependency_ids = set(self._asset_info.get(DEPENDENCY_IDS, []))
        dcc_dependency_ids = set(self._dcc_object.get(DEPENDENCY_IDS, []))

        if asset_dependency_ids != dcc_dependency_ids:
            return False

        return True

    def _sync(self) -> None:
        """
        Synchronize data from asset info to DCC object.

        Updates key synchronization fields:
        - ASSET_INFO_ID and DEPENDENCY_IDS for tracking relationships
        - ASSET_NAME, VERSION_NUMBER, COMPONENT_NAME, LOAD_MODE for metadata
        """
        if not self._dcc_object:
            return

        # Synchronize tracking and metadata fields
        self._dcc_object[ASSET_INFO_ID] = self._asset_info.get(ASSET_INFO_ID)
        self._dcc_object[DEPENDENCY_IDS] = self._asset_info.get(
            DEPENDENCY_IDS, []
        )

        # Synchronize metadata fields
        for key in [ASSET_NAME, VERSION_NUMBER, COMPONENT_NAME, LOAD_MODE]:
            if key in self._asset_info:
                self._dcc_object[key] = self._asset_info[key]

    def connect_objects(self, *args: Any, **kwargs: Any) -> None:
        """
        Connect the managed objects.

        Args:
            *args: Positional arguments for connection
            **kwargs: Keyword arguments for connection
        """
        if self._dcc_object:
            self._dcc_object.connect_objects(*args, **kwargs)

    def create_new_dcc_object(
        self,
        dcc_object_class: Type[DccObject],
        options: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> DccObject:
        """
        Create a new DCC object and set it as the managed object.

        Performs the following steps:
        1. Generates a structured name for the DCC object
        2. Ensures asset info has a unique ID (generates UUID if needed)
        3. Creates the DCC object instance via the class factory method
        4. Sets the object name and synchronizes data

        Args:
            dcc_object_class: The DCC object class to instantiate
            options: Additional options for object creation
            **kwargs: Additional keyword arguments

        Returns:
            The created DCC object
        """
        dcc_object_name = self.generate_dcc_object_name()

        # Ensure asset info has a unique ID for tracking
        if not self._asset_info.get(ASSET_INFO_ID):
            import uuid

            self._asset_info[ASSET_INFO_ID] = str(uuid.uuid4())

        # Create and configure the DCC object
        self._dcc_object = dcc_object_class.create(
            asset_info=self._asset_info, options=options, **kwargs
        )

        self._dcc_object[DCC_OBJECT_NAME] = dcc_object_name
        self._sync()

        return self._dcc_object
