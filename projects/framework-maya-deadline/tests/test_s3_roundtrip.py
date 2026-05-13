# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""S3 upload/download round-trip integration tests.

Exercises the full sync lifecycle against real AWS S3 via
:class:`S3SyncManager`:

    trace scene  ->  prepare_sync  ->  upload_files(scene_hash)
        ->  find_manifest_for_scene  ->  delete local deps
        ->  prepare_download(scene_hash)  ->  download_files
        ->  verify restored content

**Fixture randomisation:** Each test copies the versioned fixture
tree into ``tmp_path`` and injects random content into every file
(``.ma`` files get a UUID comment; binary files get 32 random
bytes).  This guarantees unique hashes per run so uploads always
hit S3 rather than matching existing CAS objects.

**S3 cleanup:** Tests do NOT delete uploaded objects.  An S3
lifecycle rule on the test bucket (7-day expiration on the
``DeadlineCloud/`` prefix) should handle cleanup.  Each run
uploads ~15 small files (~32-1300 bytes each) — negligible
storage.

Run with::

    cd projects/framework-maya-deadline
    uv run python -m pytest tests/test_s3_roundtrip.py -m deadline_cloud -v
"""

import importlib.util
import os
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from ftrack_utils.asset_tracer import TraceController

# ---------------------------------------------------------------------------
# Register MayaFileTracer for .ma files (headless, no maya.cmds).
# Same pattern as test_versioned_sync.py.
# ---------------------------------------------------------------------------

_tracer_path = (
    Path(__file__).parent.parent
    / "source"
    / "ftrack_framework_maya_deadline"
    / "tracer"
    / "maya_file_tracer.py"
)
_spec = importlib.util.spec_from_file_location(
    "maya_file_tracer", _tracer_path
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
MayaFileTracer = _mod.MayaFileTracer

TraceController.register_tracer([".ma"], MayaFileTracer)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "versioned"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _randomize_tree(src: Path, dst: Path) -> None:
    """Copy *src* to *dst*, injecting unique content into every file.

    - ``.ma`` files: append ``// test-nonce: <uuid>`` (Maya comment,
      ignored by the headless parser).
    - All other files: append 32 random bytes.

    The original *src* tree is never modified.
    """
    shutil.copytree(src, dst)
    for filepath in dst.rglob("*"):
        if not filepath.is_file():
            continue
        if filepath.suffix == ".ma":
            with open(filepath, "a") as f:
                f.write(f"// test-nonce: {uuid.uuid4()}\n")
        else:
            with open(filepath, "ab") as f:
                f.write(os.urandom(32))


def _hash_file(path):
    """Hash a file using the Deadline SDK's XXH128 algorithm."""
    from deadline.job_attachments.asset_manifests import (
        HashAlgorithm,
        hash_file,
    )

    return hash_file(str(path), HashAlgorithm.XXH128)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def randomized_scene(tmp_path):
    """Copy versioned fixtures to *tmp_path* with randomised content.

    Returns a :class:`SimpleNamespace` with:

    - ``root``: Path to the randomised ``versioned/`` directory
    - ``scene_path``: Path to ``v1/shot_010.ma``
    - ``scene_hash``: XXH128 hex digest of the randomised scene file
    - ``file_paths``: list[Path] from ``TraceController.trace().flatten()``
    - ``file_hashes``: dict mapping each resolved path (str) to its hash
    """
    dst = tmp_path / "versioned"
    _randomize_tree(FIXTURES_DIR, dst)

    scene_path = dst / "v1" / "shot_010.ma"
    scene_hash = _hash_file(scene_path)

    asset = TraceController.trace(scene_path)
    file_paths = asset.flatten()

    # Pre-compute hashes of every file for later verification.
    file_hashes = {}
    for fp in file_paths:
        resolved = fp.resolve()
        if resolved.exists():
            file_hashes[str(resolved)] = _hash_file(resolved)

    return SimpleNamespace(
        root=dst,
        scene_path=scene_path,
        scene_hash=scene_hash,
        file_paths=file_paths,
        file_hashes=file_hashes,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.deadline_cloud
class TestS3Roundtrip:
    """Full S3 upload/download round-trip tests.

    Each test is self-contained: it gets its own randomised fixture
    tree (via the function-scoped ``randomized_scene`` fixture) so
    every upload produces unique hashes.
    """

    def test_upload_all_deps(self, s3_sync_manager, randomized_scene):
        """All randomised files should need upload, then upload succeeds."""
        scene = randomized_scene
        plan = s3_sync_manager.prepare_sync(scene.file_paths)

        # Every file should need upload (unique hashes).
        assert len(plan.needs_upload) > 0
        assert len(plan.needs_upload) == len(scene.file_paths)
        assert plan.upload_size_bytes > 0

        result = s3_sync_manager.upload_files(
            plan, scene_hash=scene.scene_hash
        )
        assert result.uploaded_files > 0

    def test_manifest_has_scene_hash(self, s3_sync_manager, randomized_scene):
        """After upload, the manifest is findable by scene hash."""
        scene = randomized_scene

        # Upload first.
        plan = s3_sync_manager.prepare_sync(scene.file_paths)
        s3_sync_manager.upload_files(plan, scene_hash=scene.scene_hash)

        # Find the manifest.
        result = s3_sync_manager.find_manifest_for_scene(scene.scene_hash)
        assert (
            result is not None
        ), f"No manifest found for scene hash {scene.scene_hash}"
        _asset_root, manifest = result
        assert len(manifest.paths) > 0

    def test_reupload_is_noop(self, s3_sync_manager, randomized_scene):
        """After uploading, a second prepare_sync shows all files synced."""
        scene = randomized_scene

        # Upload.
        plan = s3_sync_manager.prepare_sync(scene.file_paths)
        s3_sync_manager.upload_files(plan, scene_hash=scene.scene_hash)

        # Re-check — everything should already be synced.
        plan2 = s3_sync_manager.prepare_sync(scene.file_paths)
        assert len(plan2.already_synced) == len(scene.file_paths)
        assert len(plan2.needs_upload) == 0
        assert plan2.upload_size_bytes == 0

    def test_download_plan_detects_missing(
        self, s3_sync_manager, randomized_scene
    ):
        """After upload + delete, prepare_download detects missing files."""
        scene = randomized_scene

        # Upload.
        plan = s3_sync_manager.prepare_sync(scene.file_paths)
        s3_sync_manager.upload_files(plan, scene_hash=scene.scene_hash)

        # Delete all dependency files (keep the scene file for root
        # derivation in prepare_download).
        deleted = []
        for fp in scene.file_paths:
            resolved = fp.resolve()
            if resolved != scene.scene_path.resolve() and resolved.exists():
                resolved.unlink()
                deleted.append(resolved)

        assert len(deleted) > 0, "Expected at least one dependency to delete"

        # Download check should find the missing files.
        dl_plan = s3_sync_manager.prepare_download(
            scene.file_paths,
            scene_hash=scene.scene_hash,
            scene_path=scene.scene_path,
        )
        assert len(dl_plan.needs_download) >= len(deleted)
        assert dl_plan.download_size_bytes > 0

    def test_download_restores_files(self, s3_sync_manager, randomized_scene):
        """Downloaded files exist and match the original hashes."""
        scene = randomized_scene

        # Upload.
        plan = s3_sync_manager.prepare_sync(scene.file_paths)
        s3_sync_manager.upload_files(plan, scene_hash=scene.scene_hash)

        # Delete deps.
        deleted_paths = []
        for fp in scene.file_paths:
            resolved = fp.resolve()
            if resolved != scene.scene_path.resolve() and resolved.exists():
                resolved.unlink()
                deleted_paths.append(str(resolved))

        # Download.
        dl_plan = s3_sync_manager.prepare_download(
            scene.file_paths,
            scene_hash=scene.scene_hash,
            scene_path=scene.scene_path,
        )
        result = s3_sync_manager.download_files(dl_plan)
        assert result.downloaded_files > 0

        # Verify every deleted file is restored with correct content.
        for path_str in deleted_paths:
            restored = Path(path_str)
            assert restored.exists(), f"File not restored: {path_str}"
            restored_hash = _hash_file(restored)
            original_hash = scene.file_hashes.get(path_str)
            if original_hash:
                assert restored_hash == original_hash, (
                    f"Hash mismatch for {path_str}: "
                    f"expected {original_hash}, got {restored_hash}"
                )

    def test_full_roundtrip(self, s3_sync_manager, randomized_scene):
        """Golden-path test: upload -> find manifest -> delete -> download -> verify."""
        scene = randomized_scene

        # 1. Trace produces files.
        assert len(scene.file_paths) > 0

        # 2. All need upload.
        plan = s3_sync_manager.prepare_sync(scene.file_paths)
        assert len(plan.needs_upload) == len(scene.file_paths)

        # 3. Upload with scene hash.
        upload_result = s3_sync_manager.upload_files(
            plan, scene_hash=scene.scene_hash
        )
        assert upload_result.uploaded_files > 0

        # 4. Manifest is findable.
        manifest_result = s3_sync_manager.find_manifest_for_scene(
            scene.scene_hash
        )
        assert manifest_result is not None

        # 5. Delete all deps (keep scene for root derivation).
        deleted = {}
        for fp in scene.file_paths:
            resolved = fp.resolve()
            if resolved != scene.scene_path.resolve() and resolved.exists():
                deleted[str(resolved)] = scene.file_hashes.get(str(resolved))
                resolved.unlink()

        assert len(deleted) > 0

        # 6. Download check detects missing.
        dl_plan = s3_sync_manager.prepare_download(
            scene.file_paths,
            scene_hash=scene.scene_hash,
            scene_path=scene.scene_path,
        )
        assert len(dl_plan.needs_download) >= len(deleted)

        # 7. Download restores files.
        dl_result = s3_sync_manager.download_files(dl_plan)
        assert dl_result.downloaded_files > 0

        # 8. Verify content.
        for path_str, original_hash in deleted.items():
            restored = Path(path_str)
            assert restored.exists(), f"Not restored: {path_str}"
            if original_hash:
                assert _hash_file(restored) == original_hash
