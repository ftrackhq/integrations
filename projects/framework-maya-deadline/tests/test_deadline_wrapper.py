# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Tests for DeadlineWrapper.

Headless tests mock the Deadline SDK so they run without AWS
credentials or Maya.  We import the wrapper module directly via
importlib to avoid the package __init__.py (which imports maya.cmds).

Integration tests (marked ``deadline_cloud``) hit the real Deadline
Cloud API and are skipped unless explicitly selected.
"""

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Import the wrapper module directly, bypassing __init__.py.
_wrapper_path = (
    Path(__file__).parent.parent
    / "source"
    / "ftrack_framework_maya_deadline"
    / "wrappers"
    / "deadline.py"
)
_spec = importlib.util.spec_from_file_location(
    "deadline_wrapper", _wrapper_path
)
_mod = importlib.util.module_from_spec(_spec)

# Patch SDK imports before exec_module so we don't need real AWS.

# Create stub modules for deadline SDK
_deadline_stub = types.ModuleType("deadline")
_deadline_client = types.ModuleType("deadline.client")
_deadline_client_api = types.ModuleType("deadline.client.api")
_deadline_client_config = types.ModuleType("deadline.client.config")
_deadline_client_config_file = types.ModuleType(
    "deadline.client.config.config_file"
)
_deadline_ja = types.ModuleType("deadline.job_attachments")
_deadline_ja_models = types.ModuleType("deadline.job_attachments.models")
_deadline_ja_upload = types.ModuleType("deadline.job_attachments.upload")

# Provide mock callables on the stubs
_deadline_client_api.get_boto3_session = MagicMock()
_deadline_client_api.list_farms = MagicMock(return_value={"farms": []})
_deadline_client_api.list_queues = MagicMock(return_value={"queues": []})
_deadline_client_api.get_queue_user_boto3_session = MagicMock()
_deadline_client_config_file.get_cache_directory = MagicMock(
    return_value="/tmp/cache"
)
_deadline_client_config_file.get_setting = MagicMock(return_value="")
_deadline_ja_models.JobAttachmentS3Settings = MagicMock
_deadline_ja_upload.S3AssetManager = MagicMock
_deadline_ja_upload.S3AssetUploader = MagicMock

# Wire up module hierarchy
_deadline_stub.client = _deadline_client
_deadline_client.api = _deadline_client_api
_deadline_client.config = _deadline_client_config
_deadline_client_config.config_file = _deadline_client_config_file
_deadline_stub.job_attachments = _deadline_ja
_deadline_ja.models = _deadline_ja_models
_deadline_ja.upload = _deadline_ja_upload

# Register stubs in sys.modules
_stubs = {
    "deadline": _deadline_stub,
    "deadline.client": _deadline_client,
    "deadline.client.api": _deadline_client_api,
    "deadline.client.config": _deadline_client_config,
    "deadline.client.config.config_file": _deadline_client_config_file,
    "deadline.job_attachments": _deadline_ja,
    "deadline.job_attachments.models": _deadline_ja_models,
    "deadline.job_attachments.upload": _deadline_ja_upload,
}

# Also need boto3 stub if not installed
try:
    import boto3  # noqa: F401
except ImportError:
    _boto3_stub = types.ModuleType("boto3")
    _boto3_stub.Session = MagicMock
    _stubs["boto3"] = _boto3_stub

_saved_modules = {}
for name, mod in _stubs.items():
    _saved_modules[name] = sys.modules.get(name)
    sys.modules[name] = mod

_spec.loader.exec_module(_mod)

# Restore original modules (if any) so we don't pollute other tests
for name, orig in _saved_modules.items():
    if orig is None:
        sys.modules.pop(name, None)
    else:
        sys.modules[name] = orig

DeadlineWrapper = _mod.DeadlineWrapper


# ---------------------------------------------------------------------------
# Headless / mocked tests
# ---------------------------------------------------------------------------


class TestGetConfiguredDefaults:
    """Test get_configured_defaults reads from deadline config."""

    def test_returns_dict_with_farm_and_queue(self):
        _mod.get_setting = MagicMock(
            side_effect=lambda key: {
                "defaults.farm_id": "farm-abc",
                "defaults.queue_id": "queue-xyz",
            }.get(key)
        )

        wrapper = DeadlineWrapper()
        result = wrapper.get_configured_defaults()

        assert result["farm_id"] == "farm-abc"
        assert result["queue_id"] == "queue-xyz"

    def test_returns_none_when_not_configured(self):
        _mod.get_setting = MagicMock(return_value="")

        wrapper = DeadlineWrapper()
        result = wrapper.get_configured_defaults()

        assert result["farm_id"] is None
        assert result["queue_id"] is None


class TestListFarms:
    """Test list_farms delegates to deadline SDK."""

    def test_returns_farms_list(self):
        farms = [
            {"farmId": "farm-1", "displayName": "Farm One"},
            {"farmId": "farm-2", "displayName": "Farm Two"},
        ]
        _mod.api.list_farms = MagicMock(return_value={"farms": farms})

        wrapper = DeadlineWrapper()
        result = wrapper.list_farms()

        assert result == farms
        _mod.api.list_farms.assert_called_once()

    def test_returns_empty_list_on_empty_response(self):
        _mod.api.list_farms = MagicMock(return_value={})

        wrapper = DeadlineWrapper()
        assert wrapper.list_farms() == []


class TestListQueues:
    """Test list_queues delegates to deadline SDK."""

    def test_returns_queues_for_farm(self):
        queues = [
            {"queueId": "queue-1", "displayName": "Queue One"},
        ]
        _mod.api.list_queues = MagicMock(return_value={"queues": queues})

        wrapper = DeadlineWrapper()
        result = wrapper.list_queues("farm-1")

        assert result == queues
        _mod.api.list_queues.assert_called_once_with(farmId="farm-1")


class TestGetQueueSettings:
    """Test get_queue_settings returns (queue, s3_settings)."""

    def test_returns_tuple(self):
        wrapper = DeadlineWrapper()
        wrapper._aws_session = MagicMock()
        mock_client = MagicMock()
        mock_client.get_queue.return_value = {
            "displayName": "Test Queue",
            "jobAttachmentSettings": {
                "s3BucketName": "bucket",
                "rootPrefix": "DeadlineCloud",
            },
        }
        wrapper._deadline = mock_client

        mock_s3_settings = MagicMock()
        _mod.JobAttachmentS3Settings = MagicMock(return_value=mock_s3_settings)

        queue, s3_settings = wrapper.get_queue_settings("farm-1", "queue-1")

        assert queue["displayName"] == "Test Queue"
        assert s3_settings is mock_s3_settings
        mock_client.get_queue.assert_called_once_with(
            farmId="farm-1", queueId="queue-1"
        )


class TestCheckSyncStatus:
    """Test check_sync_status return structure."""

    def test_returns_expected_keys(self):
        wrapper = DeadlineWrapper()
        wrapper._aws_session = MagicMock()
        mock_client = MagicMock()
        mock_client.get_queue.return_value = {
            "displayName": "Q",
            "jobAttachmentSettings": {
                "s3BucketName": "bucket",
                "rootPrefix": "DC",
            },
        }
        wrapper._deadline = mock_client

        # Mock queue session
        _mod.api.get_queue_user_boto3_session = MagicMock(
            return_value=MagicMock()
        )

        # Mock JobAttachmentS3Settings
        mock_s3_settings = MagicMock()
        mock_s3_settings.s3BucketName = "bucket"
        mock_s3_settings.rootPrefix = "DC"
        _mod.JobAttachmentS3Settings = MagicMock(return_value=mock_s3_settings)

        # Mock S3AssetManager
        mock_am = MagicMock()
        _mod.S3AssetManager = MagicMock(return_value=mock_am)

        mock_upload_group = MagicMock()
        mock_upload_group.asset_groups = []
        mock_upload_group.total_input_files = 1
        mock_upload_group.total_input_bytes = 100
        mock_am.prepare_paths_for_upload.return_value = mock_upload_group

        # Simulate one hashed file
        mock_path_obj = MagicMock()
        mock_path_obj.hash = "abc123"
        mock_path_obj.size = 100
        mock_path_obj.path = "/test/file.exr"

        mock_manifest_root = MagicMock()
        mock_manifest_root.asset_manifest.paths = [mock_path_obj]
        mock_am.hash_assets_and_create_manifest.return_value = (
            None,
            [mock_manifest_root],
        )

        _mod.get_cache_directory = MagicMock(return_value="/tmp/cache")

        # File not on S3
        mock_uploader = MagicMock()
        mock_uploader.file_already_uploaded.return_value = False
        _mod.S3AssetUploader = MagicMock(return_value=mock_uploader)

        result = wrapper.check_sync_status(
            [Path("/test/file.exr")], "farm-1", "queue-1"
        )

        assert "needs_upload" in result
        assert "already_synced" in result
        assert "total_files" in result
        assert "total_size_bytes" in result
        assert "upload_size_bytes" in result
        assert len(result["needs_upload"]) == 1
        assert len(result["already_synced"]) == 0
        assert result["total_files"] == 1
        assert result["upload_size_bytes"] == 100

    def test_already_synced_file(self):
        """File whose hash exists on S3 should be in already_synced."""
        wrapper = DeadlineWrapper()
        wrapper._aws_session = MagicMock()
        mock_client = MagicMock()
        mock_client.get_queue.return_value = {
            "displayName": "Q",
            "jobAttachmentSettings": {
                "s3BucketName": "bucket",
                "rootPrefix": "DC",
            },
        }
        wrapper._deadline = mock_client

        _mod.api.get_queue_user_boto3_session = MagicMock(
            return_value=MagicMock()
        )

        mock_s3_settings = MagicMock()
        mock_s3_settings.s3BucketName = "bucket"
        mock_s3_settings.rootPrefix = "DC"
        _mod.JobAttachmentS3Settings = MagicMock(return_value=mock_s3_settings)

        mock_am = MagicMock()
        _mod.S3AssetManager = MagicMock(return_value=mock_am)

        mock_upload_group = MagicMock()
        mock_upload_group.asset_groups = []
        mock_upload_group.total_input_files = 1
        mock_upload_group.total_input_bytes = 200
        mock_am.prepare_paths_for_upload.return_value = mock_upload_group

        mock_path_obj = MagicMock()
        mock_path_obj.hash = "already_there"
        mock_path_obj.size = 200
        mock_path_obj.path = "/test/synced.exr"

        mock_manifest_root = MagicMock()
        mock_manifest_root.asset_manifest.paths = [mock_path_obj]
        mock_am.hash_assets_and_create_manifest.return_value = (
            None,
            [mock_manifest_root],
        )

        _mod.get_cache_directory = MagicMock(return_value="/tmp/cache")

        # File IS on S3
        mock_uploader = MagicMock()
        mock_uploader.file_already_uploaded.return_value = True
        _mod.S3AssetUploader = MagicMock(return_value=mock_uploader)

        result = wrapper.check_sync_status(
            [Path("/test/synced.exr")], "farm-1", "queue-1"
        )

        assert len(result["needs_upload"]) == 0
        assert len(result["already_synced"]) == 1
        assert result["upload_size_bytes"] == 0


# ---------------------------------------------------------------------------
# Integration tests — write but do NOT run without Deadline Cloud instance
# ---------------------------------------------------------------------------


def _load_real_wrapper():
    """Load DeadlineWrapper with the real deadline SDK (no stubs)."""
    spec = importlib.util.spec_from_file_location(
        "deadline_wrapper_real", _wrapper_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DeadlineWrapper


@pytest.mark.deadline_cloud
class TestDeadlineCloudIntegration:
    """Real Deadline Cloud API tests.

    These require:
    - Deadline Cloud Monitor configured with valid credentials
    - At least one farm and queue available

    Run with: ``pytest -m deadline_cloud``
    """

    def test_list_farms_returns_non_empty(self):
        RealWrapper = _load_real_wrapper()
        wrapper = RealWrapper()
        farms = wrapper.list_farms()
        assert len(farms) > 0
        assert "farmId" in farms[0]
        assert "displayName" in farms[0]

    def test_list_queues_returns_queues(self):
        RealWrapper = _load_real_wrapper()
        wrapper = RealWrapper()
        farms = wrapper.list_farms()
        assert len(farms) > 0, "No farms available"

        queues = wrapper.list_queues(farms[0]["farmId"])
        assert len(queues) > 0
        assert "queueId" in queues[0]
        assert "displayName" in queues[0]

    def test_get_queue_settings_returns_s3_settings(self):
        RealWrapper = _load_real_wrapper()
        wrapper = RealWrapper()
        farms = wrapper.list_farms()
        assert len(farms) > 0, "No farms available"
        queues = wrapper.list_queues(farms[0]["farmId"])
        assert len(queues) > 0, "No queues available"

        queue, s3_settings = wrapper.get_queue_settings(
            farms[0]["farmId"], queues[0]["queueId"]
        )
        assert "displayName" in queue
        assert hasattr(s3_settings, "s3BucketName")
        assert hasattr(s3_settings, "rootPrefix")

    def test_get_configured_defaults_returns_dict(self):
        RealWrapper = _load_real_wrapper()
        wrapper = RealWrapper()
        defaults = wrapper.get_configured_defaults()
        assert "farm_id" in defaults
        assert "queue_id" in defaults
