# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Unit tests for ftrack_utils.aws.

SDK stubs are installed in sys.modules *before* any ftrack_utils.aws
import so that the package can resolve its deadline/boto3
dependencies.  Tests mock on the imported modules directly.
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


# -----------------------------------------------------------------------
# Install deadline + boto3 stubs BEFORE importing ftrack_utils.aws.
# The stubs remain for the lifetime of this test module.
# -----------------------------------------------------------------------

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

# NOW safe to import from ftrack_utils.aws.
from ftrack_utils.aws.models import (  # noqa: E402
    ProgressInfo,
    SyncFileEntry,
    SyncPlan,
    UploadResult,
)
from ftrack_utils.aws import s3_sync as _s3_sync_mod  # noqa: E402
from ftrack_utils.aws import deadline as _deadline_mod  # noqa: E402

S3SyncManager = _s3_sync_mod.S3SyncManager


# ===================================================================
# Model tests
# ===================================================================


class TestSyncFileEntry:
    """Verify SyncFileEntry dataclass."""

    def test_creation(self):
        entry = SyncFileEntry(path="/tex/a.exr", size=1024, hash="abc123")
        assert entry.path == "/tex/a.exr"
        assert entry.size == 1024
        assert entry.hash == "abc123"


class TestProgressInfo:
    """Verify ProgressInfo dataclass."""

    def test_creation(self):
        info = ProgressInfo(
            progress=45.2,
            message="Uploaded 1.2 GB / 2.5 GB",
            processed_files=23,
            transfer_rate=52428800.0,
        )
        assert info.progress == 45.2
        assert info.processed_files == 23
        assert info.transfer_rate == 52428800.0

    def test_zero_values(self):
        info = ProgressInfo(
            progress=0.0, message="", processed_files=0, transfer_rate=0.0
        )
        assert info.progress == 0.0


class TestUploadResult:
    """Verify UploadResult dataclass."""

    def test_creation(self):
        result = UploadResult(
            uploaded_files=10,
            uploaded_bytes=5000,
            skipped_files=5,
            skipped_bytes=2000,
            total_time=3.5,
            transfer_rate=1428.57,
        )
        assert result.uploaded_files == 10
        assert result.skipped_files == 5
        assert result.total_time == 3.5


class TestSyncPlan:
    """Verify SyncPlan dataclass and to_display_dict()."""

    def _make_plan(self, needs=None, synced=None):
        return SyncPlan(
            needs_upload=needs or [],
            already_synced=synced or [],
            total_files=(len(needs or []) + len(synced or [])),
            total_size_bytes=sum(
                e.size for e in (needs or []) + (synced or [])
            ),
            upload_size_bytes=sum(e.size for e in (needs or [])),
        )

    def test_empty_plan(self):
        plan = self._make_plan()
        assert plan.total_files == 0
        assert plan.upload_size_bytes == 0
        assert plan.to_display_dict()["needs_upload"] == []

    def test_to_display_dict_structure(self):
        """to_display_dict returns the M4-compatible format."""
        entry = SyncFileEntry(path="/a.exr", size=100, hash="abc")
        plan = self._make_plan(needs=[entry])
        d = plan.to_display_dict()

        assert "needs_upload" in d
        assert "already_synced" in d
        assert "total_files" in d
        assert "total_size_bytes" in d
        assert "upload_size_bytes" in d
        assert d["needs_upload"] == [
            {"path": "/a.exr", "size": 100, "hash": "abc"}
        ]
        assert d["total_files"] == 1
        assert d["upload_size_bytes"] == 100

    def test_to_display_dict_with_both_groups(self):
        need = SyncFileEntry(path="/a.exr", size=100, hash="abc")
        have = SyncFileEntry(path="/b.exr", size=200, hash="def")
        plan = self._make_plan(needs=[need], synced=[have])
        d = plan.to_display_dict()

        assert len(d["needs_upload"]) == 1
        assert len(d["already_synced"]) == 1
        assert d["total_files"] == 2
        assert d["total_size_bytes"] == 300
        assert d["upload_size_bytes"] == 100

    def test_internal_fields_not_in_repr(self):
        """Internal fields are excluded from repr for clean logging."""
        plan = self._make_plan()
        plan._manifests = ["mock_manifest"]
        plan._s3_bucket = "bucket"
        r = repr(plan)
        assert "_manifests" not in r
        assert "bucket" not in r


# ===================================================================
# S3SyncManager tests
# ===================================================================


class TestS3SyncManagerPrepareSync:
    """Test prepare_sync() with mocked deadline SDK."""

    def _make_manager(self):
        mock_s3_settings = MagicMock()
        mock_s3_settings.s3BucketName = "test-bucket"
        mock_s3_settings.rootPrefix = "DeadlineCloud"
        return S3SyncManager(
            "farm-1", "queue-1", mock_s3_settings, MagicMock()
        )

    def _setup_mocks(self, hashed_files, uploader_responses):
        """Configure SDK mocks for a prepare_sync call."""
        mock_am = MagicMock()
        _s3_sync_mod.S3AssetManager = MagicMock(return_value=mock_am)

        mock_upload_group = MagicMock()
        mock_upload_group.asset_groups = []
        mock_upload_group.total_input_files = len(hashed_files)
        mock_upload_group.total_input_bytes = sum(f.size for f in hashed_files)
        mock_am.prepare_paths_for_upload.return_value = mock_upload_group

        mock_manifest = MagicMock()
        mock_manifest.asset_manifest.paths = hashed_files
        mock_am.hash_assets_and_create_manifest.return_value = (
            None,
            [mock_manifest],
        )

        _s3_sync_mod.get_cache_directory = MagicMock(return_value="/tmp/cache")

        mock_uploader = MagicMock()

        def _file_check(bucket, key):
            for h, on_s3 in uploader_responses.items():
                if h in key:
                    return on_s3
            return False

        mock_uploader.file_already_uploaded.side_effect = _file_check
        _s3_sync_mod.S3AssetUploader = MagicMock(return_value=mock_uploader)

    def test_returns_sync_plan(self):
        mock_file = MagicMock()
        mock_file.hash = "abc123"
        mock_file.size = 100
        mock_file.path = "/test/file.exr"

        self._setup_mocks([mock_file], {"abc123": False})
        plan = self._make_manager().prepare_sync([Path("/test/file.exr")])

        assert isinstance(plan, SyncPlan)
        assert plan.total_files == 1
        assert plan.upload_size_bytes == 100
        assert len(plan.needs_upload) == 1
        assert plan.needs_upload[0].hash == "abc123"

    def test_already_synced_file(self):
        mock_file = MagicMock()
        mock_file.hash = "already_there"
        mock_file.size = 200
        mock_file.path = "/test/synced.exr"

        self._setup_mocks([mock_file], {"already_there": True})
        plan = self._make_manager().prepare_sync([Path("/test/synced.exr")])

        assert len(plan.needs_upload) == 0
        assert len(plan.already_synced) == 1
        assert plan.upload_size_bytes == 0

    def test_mixed_files(self):
        file_a = MagicMock()
        file_a.hash = "hash_a"
        file_a.size = 100
        file_a.path = "/a.exr"

        file_b = MagicMock()
        file_b.hash = "hash_b"
        file_b.size = 200
        file_b.path = "/b.exr"

        self._setup_mocks([file_a, file_b], {"hash_a": False, "hash_b": True})
        plan = self._make_manager().prepare_sync(
            [Path("/a.exr"), Path("/b.exr")]
        )

        assert len(plan.needs_upload) == 1
        assert len(plan.already_synced) == 1
        assert plan.needs_upload[0].path == "/a.exr"
        assert plan.already_synced[0].path == "/b.exr"
        assert plan.upload_size_bytes == 100

    def test_retains_manifests_for_upload(self):
        mock_file = MagicMock()
        mock_file.hash = "abc"
        mock_file.size = 50
        mock_file.path = "/f.exr"

        self._setup_mocks([mock_file], {"abc": False})
        plan = self._make_manager().prepare_sync([Path("/f.exr")])

        assert len(plan._manifests) == 1
        assert plan._s3_bucket == "test-bucket"
        assert plan._root_prefix == "DeadlineCloud"
        assert plan._cache_directory == "/tmp/cache"

    def test_to_display_dict_backward_compat(self):
        mock_file = MagicMock()
        mock_file.hash = "h1"
        mock_file.size = 42
        mock_file.path = "/x.exr"

        self._setup_mocks([mock_file], {"h1": False})
        plan = self._make_manager().prepare_sync([Path("/x.exr")])
        d = plan.to_display_dict()

        assert d["needs_upload"] == [
            {"path": "/x.exr", "size": 42, "hash": "h1"}
        ]
        assert d["already_synced"] == []
        assert d["total_files"] == 1
        assert d["total_size_bytes"] == 42
        assert d["upload_size_bytes"] == 42


class TestS3SyncManagerUploadFiles:
    """Test upload_files() with mocked deadline SDK."""

    def _make_manager(self):
        mock_s3_settings = MagicMock()
        mock_s3_settings.s3BucketName = "test-bucket"
        mock_s3_settings.rootPrefix = "DC"
        return S3SyncManager(
            "farm-1", "queue-1", mock_s3_settings, MagicMock()
        )

    def test_upload_returns_result(self):
        manager = self._make_manager()

        mock_stats = MagicMock()
        mock_stats.processed_files = 5
        mock_stats.processed_bytes = 5000
        mock_stats.skipped_files = 2
        mock_stats.skipped_bytes = 1000
        mock_stats.total_time = 2.5
        mock_stats.transfer_rate = 2000.0

        mock_am = MagicMock()
        mock_am.upload_assets.return_value = (mock_stats, MagicMock())
        _s3_sync_mod.S3AssetManager = MagicMock(return_value=mock_am)

        plan = SyncPlan(
            needs_upload=[SyncFileEntry("/a.exr", 100, "h1")],
            already_synced=[],
            total_files=1,
            total_size_bytes=100,
            upload_size_bytes=100,
            _manifests=["manifest_obj"],
            _s3_bucket="bucket",
            _root_prefix="DC",
            _cache_directory="/tmp/cache",
        )

        result = manager.upload_files(plan)

        assert isinstance(result, UploadResult)
        assert result.uploaded_files == 5
        assert result.uploaded_bytes == 5000
        assert result.skipped_files == 2
        assert result.total_time == 2.5
        mock_am.upload_assets.assert_called_once()

    def test_upload_empty_plan_returns_noop(self):
        manager = self._make_manager()

        plan = SyncPlan(
            needs_upload=[],
            already_synced=[SyncFileEntry("/a.exr", 100, "h1")],
            total_files=1,
            total_size_bytes=100,
            upload_size_bytes=0,
            _manifests=[],
        )

        result = manager.upload_files(plan)

        assert result.uploaded_files == 0
        assert result.uploaded_bytes == 0
        assert result.skipped_files == 1

    def test_progress_callback_bridging(self):
        manager = self._make_manager()
        received = []

        mock_stats = MagicMock()
        mock_stats.processed_files = 1
        mock_stats.processed_bytes = 100
        mock_stats.skipped_files = 0
        mock_stats.skipped_bytes = 0
        mock_stats.total_time = 1.0
        mock_stats.transfer_rate = 100.0

        mock_am = MagicMock()
        _s3_sync_mod.S3AssetManager = MagicMock(return_value=mock_am)

        def fake_upload(manifests, on_uploading_assets=None, **kwargs):
            if on_uploading_assets:
                meta = MagicMock()
                meta.progress = 50.0
                meta.progressMessage = "Uploading..."
                meta.processedFiles = 1
                meta.transferRate = 1024.0
                on_uploading_assets(meta)
            return (mock_stats, MagicMock())

        mock_am.upload_assets.side_effect = fake_upload

        plan = SyncPlan(
            needs_upload=[SyncFileEntry("/a.exr", 100, "h1")],
            already_synced=[],
            total_files=1,
            total_size_bytes=100,
            upload_size_bytes=100,
            _manifests=["m"],
            _cache_directory="/tmp/cache",
        )

        manager.upload_files(
            plan, on_progress=lambda info: received.append(info) or True
        )

        assert len(received) == 1
        assert isinstance(received[0], ProgressInfo)
        assert received[0].progress == 50.0
        assert received[0].message == "Uploading..."

    def test_cancel_via_progress_callback(self):
        manager = self._make_manager()

        mock_stats = MagicMock()
        mock_stats.processed_files = 0
        mock_stats.processed_bytes = 0
        mock_stats.skipped_files = 0
        mock_stats.skipped_bytes = 0
        mock_stats.total_time = 0.0
        mock_stats.transfer_rate = 0.0

        mock_am = MagicMock()
        _s3_sync_mod.S3AssetManager = MagicMock(return_value=mock_am)

        cancel_returned = []

        def fake_upload(manifests, on_uploading_assets=None, **kwargs):
            if on_uploading_assets:
                meta = MagicMock()
                meta.progress = 10.0
                meta.progressMessage = "Starting..."
                meta.processedFiles = 0
                meta.transferRate = 0.0
                cancel_returned.append(on_uploading_assets(meta))
            return (mock_stats, MagicMock())

        mock_am.upload_assets.side_effect = fake_upload

        plan = SyncPlan(
            needs_upload=[SyncFileEntry("/a.exr", 100, "h1")],
            already_synced=[],
            total_files=1,
            total_size_bytes=100,
            upload_size_bytes=100,
            _manifests=["m"],
            _cache_directory="/tmp/cache",
        )

        manager.upload_files(plan, on_progress=lambda info: False)

        assert cancel_returned == [False]


# ===================================================================
# Deadline function tests
# ===================================================================


class TestDeadlineFunctions:
    """Test stateless deadline config/discovery functions."""

    def test_get_configured_defaults_with_values(self):
        _deadline_mod.get_setting = MagicMock(
            side_effect=lambda key: {
                "defaults.farm_id": "farm-abc",
                "defaults.queue_id": "queue-xyz",
            }.get(key)
        )
        result = _deadline_mod.get_configured_defaults()
        assert result["farm_id"] == "farm-abc"
        assert result["queue_id"] == "queue-xyz"

    def test_get_configured_defaults_empty(self):
        _deadline_mod.get_setting = MagicMock(return_value="")
        result = _deadline_mod.get_configured_defaults()
        assert result["farm_id"] is None
        assert result["queue_id"] is None

    def test_list_farms(self):
        farms = [{"farmId": "f1", "displayName": "Farm 1"}]
        _deadline_mod.api.list_farms = MagicMock(return_value={"farms": farms})
        assert _deadline_mod.list_farms() == farms

    def test_list_farms_empty(self):
        _deadline_mod.api.list_farms = MagicMock(return_value={})
        assert _deadline_mod.list_farms() == []

    def test_list_queues(self):
        queues = [{"queueId": "q1", "displayName": "Queue 1"}]
        _deadline_mod.api.list_queues = MagicMock(
            return_value={"queues": queues}
        )
        result = _deadline_mod.list_queues("farm-1")
        assert result == queues
        _deadline_mod.api.list_queues.assert_called_once_with(farmId="farm-1")

    def test_get_queue_settings(self):
        mock_client = MagicMock()
        mock_client.get_queue.return_value = {
            "displayName": "Q1",
            "jobAttachmentSettings": {
                "s3BucketName": "bucket",
                "rootPrefix": "DC",
            },
        }
        mock_s3 = MagicMock()
        _deadline_mod.JobAttachmentS3Settings = MagicMock(return_value=mock_s3)

        queue, settings = _deadline_mod.get_queue_settings(
            mock_client, "f1", "q1"
        )

        assert queue["displayName"] == "Q1"
        assert settings is mock_s3

    def test_get_deadline_boto3_session(self):
        mock_session = MagicMock()
        _deadline_mod.get_boto3_session = MagicMock(return_value=mock_session)
        assert _deadline_mod.get_deadline_boto3_session() is mock_session
