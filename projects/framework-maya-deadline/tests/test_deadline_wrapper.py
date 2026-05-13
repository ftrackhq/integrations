# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Tests for DeadlineWrapper.

The wrapper delegates to ``ftrack_utils.aws`` which in turn calls the
deadline SDK.  Headless tests mock the ``ftrack_utils.aws`` imports on
the wrapper module so they run without AWS credentials or Maya.

We import the wrapper module directly via importlib to avoid the
package ``__init__.py`` (which imports ``maya.cmds``).

Integration tests (marked ``deadline_cloud``) hit the real Deadline
Cloud API and are skipped unless explicitly selected.
"""

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# -----------------------------------------------------------------------
# Install stubs for ftrack_utils.aws and deadline SDK before loading.
# -----------------------------------------------------------------------

# Deadline SDK stubs (needed by ftrack_utils.aws imports).
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

_deadline_stub.client = _deadline_client
_deadline_client.api = _deadline_client_api
_deadline_client.config = _deadline_client_config
_deadline_client_config.config_file = _deadline_client_config_file
_deadline_stub.job_attachments = _deadline_ja
_deadline_ja.models = _deadline_ja_models
_deadline_ja.upload = _deadline_ja_upload

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

try:
    import boto3  # noqa: F401
except ImportError:
    _boto3_stub = types.ModuleType("boto3")
    _boto3_stub.Session = MagicMock
    _stubs["boto3"] = _boto3_stub

for name, mod in _stubs.items():
    sys.modules.setdefault(name, mod)

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
_spec.loader.exec_module(_mod)

DeadlineWrapper = _mod.DeadlineWrapper

# Register MayaFileTracer for .ma files (normally done by the package __init__).
_tracer_path = (
    Path(__file__).parent.parent
    / "source"
    / "ftrack_framework_maya_deadline"
    / "tracer"
    / "maya_file_tracer.py"
)
_tracer_spec = importlib.util.spec_from_file_location(
    "maya_file_tracer", _tracer_path
)
_tracer_mod = importlib.util.module_from_spec(_tracer_spec)
_tracer_spec.loader.exec_module(_tracer_mod)

from ftrack_utils.asset_tracer import TraceController as _TC  # noqa: E402

_TC.register_tracer([".ma"], _tracer_mod.MayaFileTracer)


# ---------------------------------------------------------------------------
# Headless / mocked tests
# ---------------------------------------------------------------------------


class TestGetConfiguredDefaults:
    """Test get_configured_defaults reads from deadline config."""

    def test_returns_dict_with_farm_and_queue(self):
        _mod._get_defaults = MagicMock(
            return_value={"farm_id": "farm-abc", "queue_id": "queue-xyz"}
        )

        wrapper = DeadlineWrapper()
        result = wrapper.get_configured_defaults()

        assert result["farm_id"] == "farm-abc"
        assert result["queue_id"] == "queue-xyz"

    def test_returns_none_when_not_configured(self):
        _mod._get_defaults = MagicMock(
            return_value={"farm_id": None, "queue_id": None}
        )

        wrapper = DeadlineWrapper()
        result = wrapper.get_configured_defaults()

        assert result["farm_id"] is None
        assert result["queue_id"] is None


class TestListFarms:
    """Test list_farms delegates to ftrack_utils.aws."""

    def test_returns_farms_list(self):
        farms = [
            {"farmId": "farm-1", "displayName": "Farm One"},
            {"farmId": "farm-2", "displayName": "Farm Two"},
        ]
        _mod._list_farms = MagicMock(return_value=farms)

        wrapper = DeadlineWrapper()
        result = wrapper.list_farms()

        assert result == farms
        _mod._list_farms.assert_called_once()

    def test_returns_empty_list_on_empty_response(self):
        _mod._list_farms = MagicMock(return_value=[])

        wrapper = DeadlineWrapper()
        assert wrapper.list_farms() == []


class TestListQueues:
    """Test list_queues delegates to ftrack_utils.aws."""

    def test_returns_queues_for_farm(self):
        queues = [
            {"queueId": "queue-1", "displayName": "Queue One"},
        ]
        _mod._list_queues = MagicMock(return_value=queues)

        wrapper = DeadlineWrapper()
        result = wrapper.list_queues("farm-1")

        assert result == queues
        _mod._list_queues.assert_called_once_with("farm-1")


class TestGetQueueSettings:
    """Test get_queue_settings returns (queue, s3_settings)."""

    def test_returns_tuple(self):
        wrapper = DeadlineWrapper()
        wrapper._aws_session = MagicMock()
        wrapper._deadline = MagicMock()

        mock_s3_settings = MagicMock()
        _mod._get_queue_settings = MagicMock(
            return_value=(
                {"displayName": "Test Queue"},
                mock_s3_settings,
            )
        )

        queue, s3_settings = wrapper.get_queue_settings("farm-1", "queue-1")

        assert queue["displayName"] == "Test Queue"
        assert s3_settings is mock_s3_settings


class TestCheckSyncStatus:
    """Test check_sync_status return structure."""

    def _setup_wrapper_with_mock_manager(self, plan_dict):
        """Return a wrapper whose sync manager returns *plan_dict*."""
        from ftrack_utils.aws.models import SyncFileEntry, SyncPlan

        needs = [SyncFileEntry(**e) for e in plan_dict.get("needs_upload", [])]
        synced = [
            SyncFileEntry(**e) for e in plan_dict.get("already_synced", [])
        ]
        plan = SyncPlan(
            needs_upload=needs,
            already_synced=synced,
            total_files=plan_dict["total_files"],
            total_size_bytes=plan_dict["total_size_bytes"],
            upload_size_bytes=plan_dict["upload_size_bytes"],
        )

        mock_manager = MagicMock()
        mock_manager.prepare_sync.return_value = plan

        wrapper = DeadlineWrapper()
        wrapper._aws_session = MagicMock()
        wrapper._deadline = MagicMock()

        # Mock _get_sync_manager to return our mock.
        wrapper._get_sync_manager = MagicMock(return_value=mock_manager)

        return wrapper

    def test_returns_expected_keys(self, tmp_path):
        test_file = tmp_path / "file.exr"
        test_file.write_bytes(b"data")
        wrapper = self._setup_wrapper_with_mock_manager(
            {
                "needs_upload": [
                    {"path": str(test_file), "size": 100, "hash": "abc123"}
                ],
                "already_synced": [],
                "total_files": 1,
                "total_size_bytes": 100,
                "upload_size_bytes": 100,
            }
        )

        result = wrapper.check_sync_status([test_file], "farm-1", "queue-1")

        assert "needs_upload" in result
        assert "already_synced" in result
        assert "total_files" in result
        assert "total_size_bytes" in result
        assert "upload_size_bytes" in result
        assert len(result["needs_upload"]) == 1
        assert len(result["already_synced"]) == 0
        assert result["total_files"] == 1
        assert result["upload_size_bytes"] == 100

    def test_already_synced_file(self, tmp_path):
        """File whose hash exists on S3 should be in already_synced."""
        test_file = tmp_path / "synced.exr"
        test_file.write_bytes(b"data")
        wrapper = self._setup_wrapper_with_mock_manager(
            {
                "needs_upload": [],
                "already_synced": [
                    {
                        "path": str(test_file),
                        "size": 200,
                        "hash": "already_there",
                    }
                ],
                "total_files": 1,
                "total_size_bytes": 200,
                "upload_size_bytes": 0,
            }
        )

        result = wrapper.check_sync_status([test_file], "farm-1", "queue-1")

        assert len(result["needs_upload"]) == 0
        assert len(result["already_synced"]) == 1
        assert result["upload_size_bytes"] == 0


class TestUploadFiles:
    """Test upload_files delegates to S3SyncManager."""

    def test_upload_files_delegates_to_sync_manager(self):
        from ftrack_utils.aws.models import (
            SyncFileEntry,
            SyncPlan,
            UploadResult,
        )

        plan = SyncPlan(
            needs_upload=[SyncFileEntry("/a.exr", 100, "h1")],
            already_synced=[],
            total_files=1,
            total_size_bytes=100,
            upload_size_bytes=100,
            _manifests=["m"],
        )

        mock_result = UploadResult(
            uploaded_files=1,
            uploaded_bytes=100,
            skipped_files=0,
            skipped_bytes=0,
            total_time=1.0,
            transfer_rate=100.0,
        )

        mock_manager = MagicMock()
        mock_manager.upload_files.return_value = mock_result

        wrapper = DeadlineWrapper()
        wrapper._sync_manager = mock_manager
        wrapper._last_plan = plan

        result = wrapper.upload_files()

        assert result.uploaded_files == 1
        mock_manager.upload_files.assert_called_once_with(
            plan, None, scene_hash=None
        )

    def test_upload_files_without_plan_raises(self):
        wrapper = DeadlineWrapper()
        with pytest.raises(RuntimeError, match="No sync plan"):
            wrapper.upload_files()

    def test_upload_files_without_manager_raises(self):
        from ftrack_utils.aws.models import SyncPlan

        wrapper = DeadlineWrapper()
        wrapper._last_plan = SyncPlan(
            needs_upload=[],
            already_synced=[],
            total_files=0,
            total_size_bytes=0,
            upload_size_bytes=0,
        )
        with pytest.raises(RuntimeError, match="No sync manager"):
            wrapper.upload_files()

    def test_upload_files_passes_progress_callback(self):
        from ftrack_utils.aws.models import (
            SyncFileEntry,
            SyncPlan,
            UploadResult,
        )

        plan = SyncPlan(
            needs_upload=[SyncFileEntry("/a.exr", 100, "h1")],
            already_synced=[],
            total_files=1,
            total_size_bytes=100,
            upload_size_bytes=100,
            _manifests=["m"],
        )

        mock_manager = MagicMock()
        mock_manager.upload_files.return_value = UploadResult(
            uploaded_files=1,
            uploaded_bytes=100,
            skipped_files=0,
            skipped_bytes=0,
            total_time=1.0,
            transfer_rate=100.0,
        )

        wrapper = DeadlineWrapper()
        wrapper._sync_manager = mock_manager
        wrapper._last_plan = plan

        cb = MagicMock()
        wrapper.upload_files(on_progress=cb)

        mock_manager.upload_files.assert_called_once_with(
            plan, cb, scene_hash=None
        )


# ---------------------------------------------------------------------------
# Sync flow tests — verify upload/download/compare using temp files.
# ---------------------------------------------------------------------------


class TestSyncFlow:
    """End-to-end tests for the check_sync_status upload/download flow.

    Uses real temp files and a mock S3SyncManager to verify that:
    - All traced files (including deps) are passed to prepare_sync
    - Missing files are passed to prepare_download
    - Results are merged correctly in the returned dict
    """

    def _make_scene_with_deps(self, tmp_path):
        """Create a minimal .ma scene with dependencies."""
        shared = tmp_path / "shared"
        shared.mkdir()
        scene_dir = tmp_path / "v1"
        scene_dir.mkdir()

        # Scene file
        scene = scene_dir / "shot.ma"
        scene.write_text(
            "//Maya ASCII 2025 scene\n"
            'requires maya "2025";\n'
            'file -r -ns "room" -dr 1 -rfn "roomRN"\n'
            '         -typ "mayaAscii" "../shared/room.ma";\n'
            'createNode file -n "tex";\n'
            '    setAttr ".fileTextureName" -type "string"'
            ' "../shared/diffuse.exr";\n'
            'createNode AlembicNode -n "cache";\n'
            '    setAttr ".abc_File" -type "string" "anim.abc";\n'
        )

        # Dependencies
        ref = shared / "room.ma"
        ref.write_text(
            "//Maya ASCII 2025 scene\n"
            'requires maya "2025";\n'
            'createNode file -n "woodTex";\n'
            '    setAttr ".fileTextureName" -type "string"'
            ' "wood.exr";\n'
        )
        (shared / "diffuse.exr").write_bytes(b"exr-data")
        (shared / "wood.exr").write_bytes(b"wood-exr")
        (scene_dir / "anim.abc").write_bytes(b"abc-data")

        return scene

    def _make_wrapper(self, prepare_sync_result, prepare_download_result):
        """Create wrapper with mocked sync manager."""
        mock_manager = MagicMock()
        mock_manager.prepare_sync.return_value = prepare_sync_result
        mock_manager.prepare_download.return_value = prepare_download_result

        wrapper = DeadlineWrapper()
        wrapper._aws_session = MagicMock()
        wrapper._deadline = MagicMock()
        wrapper._get_sync_manager = MagicMock(return_value=mock_manager)

        return wrapper, mock_manager

    def test_all_files_passed_to_prepare_sync_when_all_exist(self, tmp_path):
        """When all files exist, prepare_sync receives all of them."""
        from ftrack_utils.aws.models import SyncFileEntry, SyncPlan

        scene = self._make_scene_with_deps(tmp_path)

        # Trace the scene
        from ftrack_utils.asset_tracer import TraceController

        asset = TraceController.trace(scene)
        file_paths = asset.flatten()

        # All should exist
        assert all(p.exists() for p in file_paths)
        assert len(file_paths) == 5  # scene + room.ma + diffuse + wood + abc

        plan = SyncPlan(
            needs_upload=[
                SyncFileEntry(path=str(p), size=10, hash="h")
                for p in file_paths
            ],
            already_synced=[],
            total_files=len(file_paths),
            total_size_bytes=50,
            upload_size_bytes=50,
        )
        dl_plan = SyncPlan(needs_upload=[], already_synced=[])

        wrapper, mock_mgr = self._make_wrapper(plan, dl_plan)
        wrapper.check_sync_status(file_paths, "farm-1", "queue-1")

        # prepare_sync called with all resolved paths
        call_args = mock_mgr.prepare_sync.call_args[0][0]
        assert len(call_args) == 5

    def test_missing_files_passed_to_prepare_download(self, tmp_path):
        """When some files are deleted, they go to prepare_download."""
        from ftrack_utils.aws.models import SyncFileEntry, SyncPlan

        scene = self._make_scene_with_deps(tmp_path)

        from ftrack_utils.asset_tracer import TraceController

        asset = TraceController.trace(scene)
        file_paths = asset.flatten()
        assert len(file_paths) == 5

        # Delete two deps
        shared = tmp_path / "shared"
        (shared / "diffuse.exr").unlink()
        (shared / "wood.exr").unlink()

        existing = [p.resolve() for p in file_paths if p.exists()]
        missing = [p.resolve() for p in file_paths if not p.exists()]
        assert len(existing) == 3
        assert len(missing) == 2

        upload_plan = SyncPlan(
            needs_upload=[],
            already_synced=[
                SyncFileEntry(path=str(p), size=10, hash="h") for p in existing
            ],
            total_files=len(existing),
            total_size_bytes=30,
            upload_size_bytes=0,
        )
        dl_plan = SyncPlan(
            needs_upload=[],
            already_synced=[],
            needs_download=[
                SyncFileEntry(path=str(p), size=10, hash="h") for p in missing
            ],
            download_size_bytes=20,
        )

        wrapper, mock_mgr = self._make_wrapper(upload_plan, dl_plan)
        result = wrapper.check_sync_status(
            file_paths, "farm-1", "queue-1", scene_hash="abc123"
        )

        # prepare_sync called with only existing files
        sync_call = mock_mgr.prepare_sync.call_args[0][0]
        assert len(sync_call) == 3

        # prepare_download called with ALL file paths + scene_hash
        dl_call_args = mock_mgr.prepare_download.call_args
        assert len(dl_call_args[0][0]) == 5  # all file_paths
        assert dl_call_args[1]["scene_hash"] == "abc123"

        # Result dict contains both upload and download info
        assert len(result["needs_download"]) == 2
        assert result["download_size_bytes"] == 20

    def test_result_dict_has_needs_download_key(self, tmp_path):
        """Result dict always contains needs_download key."""
        from ftrack_utils.aws.models import SyncPlan

        scene = self._make_scene_with_deps(tmp_path)

        from ftrack_utils.asset_tracer import TraceController

        file_paths = TraceController.trace(scene).flatten()

        plan = SyncPlan(needs_upload=[], already_synced=[])
        dl_plan = SyncPlan(needs_upload=[], already_synced=[])
        wrapper, _ = self._make_wrapper(plan, dl_plan)

        result = wrapper.check_sync_status(file_paths, "farm-1", "queue-1")

        assert "needs_download" in result
        assert "download_size_bytes" in result

    def test_deleted_reference_appears_in_trace(self, tmp_path):
        """Deleted .ma reference is preserved in trace (not silently lost)."""
        scene = self._make_scene_with_deps(tmp_path)

        from ftrack_utils.asset_tracer import TraceController

        # Trace with everything present
        all_paths = TraceController.trace(scene).flatten()
        assert len(all_paths) == 5

        # Delete the referenced .ma file
        ref = tmp_path / "shared" / "room.ma"
        ref.unlink()

        # Re-trace — room.ma should still appear (preserved by controller)
        partial_paths = TraceController.trace(scene).flatten()

        # room.ma should be in the trace even though it doesn't exist
        room_names = [p.name for p in partial_paths]
        assert "room.ma" in room_names, (
            f"Deleted reference 'room.ma' was silently dropped. "
            f"Got: {room_names}"
        )

    def test_deleted_deps_not_in_needs_upload(self, tmp_path):
        """Deleted files should NOT be passed to prepare_sync."""
        from ftrack_utils.aws.models import SyncPlan

        scene = self._make_scene_with_deps(tmp_path)

        from ftrack_utils.asset_tracer import TraceController

        file_paths = TraceController.trace(scene).flatten()

        # Delete two files
        (tmp_path / "shared" / "diffuse.exr").unlink()
        (tmp_path / "v1" / "anim.abc").unlink()

        plan = SyncPlan(needs_upload=[], already_synced=[])
        dl_plan = SyncPlan(needs_upload=[], already_synced=[])
        wrapper, mock_mgr = self._make_wrapper(plan, dl_plan)

        wrapper.check_sync_status(file_paths, "farm-1", "queue-1")

        # prepare_sync should only receive files that exist
        sync_paths = mock_mgr.prepare_sync.call_args[0][0]
        for p in sync_paths:
            assert p.exists(), f"Non-existent file passed to prepare_sync: {p}"

    def test_paths_are_resolved(self, tmp_path):
        """Paths with ../ are resolved before passing to SDK."""
        from ftrack_utils.aws.models import SyncPlan

        scene = self._make_scene_with_deps(tmp_path)

        from ftrack_utils.asset_tracer import TraceController

        file_paths = TraceController.trace(scene).flatten()

        # Some paths have ../ (e.g., v1/../shared/room.ma)
        has_dotdot = any(".." in str(p) for p in file_paths)
        assert has_dotdot, "Test expects paths with ../ from tracer"

        plan = SyncPlan(needs_upload=[], already_synced=[])
        dl_plan = SyncPlan(needs_upload=[], already_synced=[])
        wrapper, mock_mgr = self._make_wrapper(plan, dl_plan)

        wrapper.check_sync_status(file_paths, "farm-1", "queue-1")

        # All paths passed to prepare_sync should be resolved (no ../)
        sync_paths = mock_mgr.prepare_sync.call_args[0][0]
        for p in sync_paths:
            assert ".." not in str(p), f"Unresolved path: {p}"


# ---------------------------------------------------------------------------
# Integration tests — require real Deadline Cloud instance.
#
# All tests use session-scoped fixtures from conftest.py that
# validate credentials, farms, queues, and S3 settings once at
# startup.  If anything is wrong the entire session fails
# immediately with a clear error — no false positives.
#
# Run with: ``pytest -m deadline_cloud``
# ---------------------------------------------------------------------------


@pytest.mark.deadline_cloud
class TestDeadlineCloudIntegration:
    """Real Deadline Cloud API tests.

    All tests use session-scoped fixtures from ``conftest.py`` that
    validate credentials + farm + queue + S3 once at startup.  If
    any precondition fails, every test in this class errors
    immediately — no false positives from empty API responses.

    Run with: ``pytest -m deadline_cloud``
    """

    def test_list_farms_has_expected_keys(self, deadline_farm):
        """Farm dict contains farmId and displayName."""
        assert "farmId" in deadline_farm
        assert "displayName" in deadline_farm

    def test_list_queues_has_expected_keys(
        self, deadline_wrapper, deadline_farm, deadline_queue
    ):
        """Queue dict contains queueId and displayName."""
        queues = deadline_wrapper.list_queues(deadline_farm["farmId"])
        assert len(queues) > 0
        assert "queueId" in deadline_queue
        assert "displayName" in deadline_queue

    def test_queue_has_s3_settings(self, deadline_s3_settings):
        """Queue settings include a non-empty S3 bucket and root prefix."""
        queue, s3_settings = deadline_s3_settings
        assert "displayName" in queue
        assert s3_settings.s3BucketName
        assert s3_settings.rootPrefix
