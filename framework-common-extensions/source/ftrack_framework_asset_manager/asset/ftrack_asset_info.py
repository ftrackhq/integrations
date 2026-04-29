# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""
Ftrack Asset Info Module

This module provides the FtrackAssetInfo class which represents asset metadata
and maintains backward compatibility with dict-based access patterns.
"""

import base64
import json
import logging
from typing import Any, Dict, Optional, Union

from ftrack_framework_asset_manager.asset.constants import *


logger = logging.getLogger(__name__)


class FtrackAssetInfo(dict):
    """
    Asset information container that maintains dict compatibility.

    This class represents asset metadata and provides methods for creating
    instances from ftrack entities and encoding/decoding options for DCC
    node attributes.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the asset info with provided data."""
        super().__init__(*args, **kwargs)

        # Ensure all required keys are present with default values
        for key in KEYS:
            if key not in self:
                self[key] = None

    @classmethod
    def create(
        cls,
        asset_version_entity: Optional[Dict[str, Any]] = None,
        component_entity: Optional[Dict[str, Any]] = None,
        load_mode: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        reference_object: Optional[str] = None,
        is_latest_version: Optional[bool] = None,
        asset_info_id: Optional[str] = None,
        dependency_ids: Optional[list] = None,
        objects_loaded: Optional[bool] = None,
        dcc_object_name: Optional[str] = None,
        session: Optional[Any] = None,
    ) -> "FtrackAssetInfo":
        """
        Create an FtrackAssetInfo instance from ftrack entities.

        Args:
            asset_version_entity: The ftrack AssetVersion entity
            component_entity: The ftrack Component entity
            load_mode: The load mode for the asset
            options: Additional options dictionary
            reference_object: Reference object identifier
            is_latest_version: Whether this is the latest version
            asset_info_id: Unique identifier for this asset info
            dependency_ids: List of dependency IDs
            objects_loaded: Whether objects have been loaded
            dcc_object_name: Name of the DCC object
            session: ftrack_api session object

        Returns:
            FtrackAssetInfo instance
        """
        asset_info = cls()

        # Set basic asset information
        if asset_version_entity:
            asset_info[ASSET_ID] = asset_version_entity.get("asset_id")
            asset_info[ASSET_NAME] = asset_version_entity.get("name")
            asset_info[VERSION_ID] = asset_version_entity.get("id")
            asset_info[VERSION_NUMBER] = asset_version_entity.get("version")

            # Get asset type name from the parent asset
            if session and asset_info[ASSET_ID]:
                try:
                    asset_entity = session.get("Asset", asset_info[ASSET_ID])
                    asset_info[ASSET_TYPE_NAME] = asset_entity.get(
                        "type", {}
                    ).get("name")
                except Exception as e:
                    logger.warning(f"Failed to get asset type: {e}")
                    asset_info[ASSET_TYPE_NAME] = None

            # Get context path
            context_id = asset_version_entity.get("context_id")
            if session and context_id:
                try:
                    context_entity = session.get("Context", context_id)
                    asset_info[CONTEXT_PATH] = context_entity.get("path")
                except Exception as e:
                    logger.warning(f"Failed to get context path: {e}")
                    asset_info[CONTEXT_PATH] = None

        # Set component information
        if component_entity:
            asset_info[COMPONENT_ID] = component_entity.get("id")
            asset_info[COMPONENT_NAME] = component_entity.get("name")
            asset_info[COMPONENT_PATH] = component_entity.get("file_type")

        # Set additional properties
        if load_mode:
            asset_info[LOAD_MODE] = load_mode

        if options:
            asset_info[ASSET_INFO_OPTIONS] = options
        else:
            asset_info[ASSET_INFO_OPTIONS] = {}

        if reference_object:
            asset_info[REFERENCE_OBJECT] = reference_object

        if is_latest_version is not None:
            asset_info[IS_LATEST_VERSION] = is_latest_version

        if asset_info_id:
            asset_info[ASSET_INFO_ID] = asset_info_id

        if dependency_ids:
            asset_info[DEPENDENCY_IDS] = dependency_ids
        else:
            asset_info[DEPENDENCY_IDS] = []

        if objects_loaded is not None:
            asset_info[OBJECTS_LOADED] = objects_loaded

        if dcc_object_name:
            asset_info[DCC_OBJECT_NAME] = dcc_object_name

        return asset_info

    def encode_options(self) -> str:
        """
        Encode the options dictionary as a base64 string for DCC node attributes.

        Returns:
            Base64 encoded string representation of options
        """
        if not self[ASSET_INFO_OPTIONS]:
            return ""

        try:
            # Convert options dict to JSON string, then to bytes
            options_json = json.dumps(self[ASSET_INFO_OPTIONS])
            options_bytes = options_json.encode('utf-8')

            # Base64 encode
            encoded = base64.b64encode(options_bytes).decode('utf-8')
            return encoded
        except Exception as e:
            logger.error(f"Failed to encode options: {e}")
            return ""

    def decode_options(self, encoded_options: str) -> Dict[str, Any]:
        """
        Decode base64 encoded options string back to dictionary.

        Args:
            encoded_options: Base64 encoded options string

        Returns:
            Decoded options dictionary
        """
        if not encoded_options:
            return {}

        try:
            # Base64 decode
            options_bytes = base64.b64decode(encoded_options.encode('utf-8'))

            # Convert bytes to JSON string, then to dict
            options_json = options_bytes.decode('utf-8')
            options_dict = json.loads(options_json)

            self[ASSET_INFO_OPTIONS] = options_dict
            return options_dict
        except Exception as e:
            logger.error(f"Failed to decode options: {e}")
            return {}

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
