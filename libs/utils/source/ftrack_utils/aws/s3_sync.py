# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""S3 sync check, upload, and download orchestration.

DCC-agnostic.  Accepts pre-configured Deadline Cloud credentials and
file paths; knows nothing about Maya, Nuke, etc.

Typical usage::

    manager = S3SyncManager(farm_id, queue_id, s3_settings, queue_session)
    plan = manager.prepare_sync(file_paths)     # hash + S3 HEAD checks
    result = manager.upload_files(plan)          # upload missing files

    # Download flow:
    plan = manager.prepare_download(file_paths)  # check local vs manifest
    result = manager.download_files(plan)         # download missing files
"""

import logging
from pathlib import Path
from typing import Callable, Optional

from deadline.client.config.config_file import get_cache_directory
from deadline.job_attachments.models import JobAttachmentS3Settings
from deadline.job_attachments.upload import S3AssetManager, S3AssetUploader

from .models import (
    DownloadResult,
    ProgressInfo,
    SyncFileEntry,
    SyncPlan,
    UploadResult,
)

# Lazy imports for download (avoid breaking test stubs):
# - deadline.job_attachments.asset_manifests.decode_manifest
# - deadline.job_attachments.download.download_files_from_manifests
# - deadline.job_attachments.models.FileConflictResolution

logger = logging.getLogger(__name__)


class S3SyncManager:
    """Orchestrates file hashing, S3 status checks, and uploads.

    Each instance is bound to a specific farm/queue/session
    combination.  Create a new instance when the user selects a
    different queue.
    """

    def __init__(
        self,
        farm_id: str,
        queue_id: str,
        s3_settings: JobAttachmentS3Settings,
        queue_session,
    ):
        self._farm_id = farm_id
        self._queue_id = queue_id
        self._s3_settings = s3_settings
        self._queue_session = queue_session

    # -- Sync check ------------------------------------------------------

    def prepare_sync(self, file_paths: list[Path]) -> SyncPlan:
        """Hash files (XXH128), check S3 existence, return a plan.

        The returned :class:`SyncPlan` retains the internal manifests
        so that :meth:`upload_files` can proceed without re-hashing.

        Args:
            file_paths: Absolute paths to check.

        Returns:
            A :class:`SyncPlan` with display data and internal state.
        """
        s3_bucket = self._s3_settings.s3BucketName
        root_prefix = self._s3_settings.rootPrefix

        # Hash files and create local manifests (in memory only)
        logger.info("Hashing %d files...", len(file_paths))
        asset_manager = S3AssetManager(
            farm_id=self._farm_id,
            queue_id=self._queue_id,
            job_attachment_settings=self._s3_settings,
            session=self._queue_session,
        )

        upload_group = asset_manager.prepare_paths_for_upload(
            file_paths,
            [],  # no output directories
            [],  # no referenced paths
        )

        cache_directory = get_cache_directory()
        (_, manifests) = asset_manager.hash_assets_and_create_manifest(
            upload_group.asset_groups,
            upload_group.total_input_files,
            upload_group.total_input_bytes,
            cache_directory,
        )

        # Collect all hashed file entries from manifests, pairing
        # each with the asset root so we can reconstruct absolute paths.
        hashed_files = []  # list of (root_path, manifest_path_obj)
        for manifest_root in manifests:
            if not manifest_root.asset_manifest:
                continue
            root = manifest_root.root_path or ""
            for path_obj in manifest_root.asset_manifest.paths:
                hashed_files.append((root, path_obj))

        logger.info(
            "Hashing complete: %d file(s). Checking S3 existence...",
            len(hashed_files),
        )

        # Check S3 existence per hash
        uploader = S3AssetUploader(
            session=self._queue_session,
            s3_max_pool_connections=50,
            small_file_threshold_multiplier=20,
        )
        needs_upload = []
        already_synced = []
        upload_size = 0
        total_size = 0

        for root, path_obj in hashed_files:
            file_size = path_obj.size if hasattr(path_obj, "size") else 0
            file_hash = path_obj.hash if hasattr(path_obj, "hash") else ""
            rel_path = str(path_obj.path) if hasattr(path_obj, "path") else ""
            # Reconstruct absolute path from asset root + relative.
            if root:
                file_path = str((Path(root) / rel_path).resolve())
            else:
                file_path = rel_path
            total_size += file_size

            s3_key = f"{root_prefix}/Data/{file_hash}.xxh128"

            try:
                on_s3 = uploader.file_already_uploaded(s3_bucket, s3_key)
            except Exception:
                logger.warning(
                    "S3 check failed for %s — assuming needs upload",
                    file_hash,
                    exc_info=True,
                )
                on_s3 = False

            entry = SyncFileEntry(
                path=file_path, size=file_size, hash=file_hash
            )
            if on_s3:
                already_synced.append(entry)
            else:
                needs_upload.append(entry)
                upload_size += file_size

        logger.info(
            "Sync check complete: %d need upload (%s bytes), "
            "%d already synced",
            len(needs_upload),
            f"{upload_size:,}",
            len(already_synced),
        )

        return SyncPlan(
            needs_upload=needs_upload,
            already_synced=already_synced,
            total_files=len(hashed_files),
            total_size_bytes=total_size,
            upload_size_bytes=upload_size,
            _manifests=list(manifests),
            _s3_bucket=s3_bucket,
            _root_prefix=root_prefix,
            _cache_directory=cache_directory,
        )

    # -- Upload ----------------------------------------------------------

    def upload_files(
        self,
        plan: SyncPlan,
        on_progress: Optional[Callable[[ProgressInfo], bool]] = None,
        scene_hash: Optional[str] = None,
    ) -> UploadResult:
        """Upload files from a prepared :class:`SyncPlan`.

        Calls ``S3AssetManager.upload_assets()`` with the manifests
        retained by :meth:`prepare_sync`.

        Args:
            plan: A :class:`SyncPlan` from :meth:`prepare_sync`.
            on_progress: Optional callback receiving
                :class:`ProgressInfo` snapshots.  Return *False* to
                cancel the upload (the SDK raises
                ``AssetSyncCancelledError``).

        Returns:
            An :class:`UploadResult` with summary statistics.
        """
        if not plan._manifests:
            logger.info("Nothing to upload — all files already synced.")
            return UploadResult(
                uploaded_files=0,
                uploaded_bytes=0,
                skipped_files=plan.total_files,
                skipped_bytes=plan.total_size_bytes,
                total_time=0.0,
                transfer_rate=0.0,
            )

        logger.info(
            "Uploading %d file(s) (%s bytes)...",
            len(plan.needs_upload),
            f"{plan.upload_size_bytes:,}",
        )

        # Wrap the caller's progress callback into the SDK's expected
        # signature: Callable[[ProgressReportMetadata], bool].
        sdk_callback = None
        if on_progress is not None:

            def sdk_callback(metadata):
                info = ProgressInfo(
                    progress=metadata.progress,
                    message=metadata.progressMessage,
                    processed_files=metadata.processedFiles,
                    transfer_rate=metadata.transferRate,
                )
                return on_progress(info)

        asset_manager = S3AssetManager(
            farm_id=self._farm_id,
            queue_id=self._queue_id,
            job_attachment_settings=self._s3_settings,
            session=self._queue_session,
        )

        (stats, attachments) = asset_manager.upload_assets(
            plan._manifests,
            on_uploading_assets=sdk_callback,
            s3_check_cache_dir=plan._cache_directory,
        )

        # Store scene hash as S3 metadata on the manifest object
        # so it can be matched later during download.
        if scene_hash and attachments.manifests:
            s3_bucket = self._s3_settings.s3BucketName
            s3 = self._queue_session.client("s3")
            for mp in attachments.manifests:
                if mp.inputManifestPath:
                    full_key = (
                        self._s3_settings.add_root_and_manifest_folder_prefix(
                            mp.inputManifestPath
                        )
                    )
                    try:
                        head = s3.head_object(Bucket=s3_bucket, Key=full_key)
                        metadata = head.get("Metadata", {})
                        metadata["scene-hash"] = scene_hash
                        s3.copy_object(
                            Bucket=s3_bucket,
                            CopySource={
                                "Bucket": s3_bucket,
                                "Key": full_key,
                            },
                            Key=full_key,
                            Metadata=metadata,
                            MetadataDirective="REPLACE",
                        )
                        logger.info(
                            "Stored scene-hash %s on manifest %s",
                            scene_hash,
                            full_key,
                        )
                    except Exception:
                        logger.warning(
                            "Failed to store scene-hash on manifest",
                            exc_info=True,
                        )

        logger.info(
            "Upload complete: %d file(s), %s bytes in %.1fs (%.1f MB/s)",
            stats.processed_files,
            f"{stats.processed_bytes:,}",
            stats.total_time,
            stats.transfer_rate / (1024 * 1024) if stats.transfer_rate else 0,
        )

        return UploadResult(
            uploaded_files=stats.processed_files,
            uploaded_bytes=stats.processed_bytes,
            skipped_files=stats.skipped_files,
            skipped_bytes=stats.skipped_bytes,
            total_time=stats.total_time,
            transfer_rate=stats.transfer_rate,
        )

    # -- Manifest matching -----------------------------------------------

    def find_manifest_for_scene(self, scene_hash):
        """Find the manifest whose ``scene-hash`` metadata matches.

        Lists manifest keys in S3, HEADs each to read metadata,
        and downloads + decodes only the matching one.

        Args:
            scene_hash: XXH128 hex digest of the scene file.

        Returns:
            ``(asset_root, BaseAssetManifest)`` or *None* if no match.
        """
        s3_bucket = self._s3_settings.s3BucketName
        # Build prefix WITHOUT the random GUID — we want to search
        # all manifests for this farm/queue, not a specific upload.
        manifest_prefix = (
            self._s3_settings.add_root_and_manifest_folder_prefix(
                f"{self._farm_id}/{self._queue_id}/Inputs"
            )
        )

        s3 = self._queue_session.client("s3")

        # List all manifest keys under the Inputs prefix.
        keys = []
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=s3_bucket, Prefix=manifest_prefix
        ):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])

        logger.info(
            "Searching %d manifest(s) for scene-hash %s",
            len(keys),
            scene_hash,
        )

        # HEAD each manifest to check scene-hash metadata.
        for key in keys:
            try:
                head = s3.head_object(Bucket=s3_bucket, Key=key)
                metadata = head.get("Metadata", {})
                if metadata.get("scene-hash") == scene_hash:
                    logger.info("Matched manifest: %s", key)
                    # Download and decode this one manifest.
                    response = s3.get_object(Bucket=s3_bucket, Key=key)
                    body = response["Body"].read().decode("utf-8")

                    from deadline.job_attachments.download import (
                        decode_manifest,
                    )

                    manifest = decode_manifest(body)
                    asset_root = metadata.get("asset-root", "")
                    return (asset_root, manifest)
            except Exception:
                logger.debug("Failed to HEAD manifest %s", key, exc_info=True)

        logger.info("No manifest matched scene-hash %s", scene_hash)
        return None

    # -- Download check --------------------------------------------------

    def prepare_download(
        self,
        file_paths: list[Path],
        scene_hash: Optional[str] = None,
        scene_path: Optional[Path] = None,
    ) -> SyncPlan:
        """Check which files need downloading from S3.

        Uses two complementary sources:

        1. **Manifest** (if *scene_hash* is provided): find the
           manifest tagged with that hash via HEAD requests, then
           check ALL files in it against the local filesystem.
           This covers the complete dependency tree from the
           original upload — even files the local tracer can't
           discover (e.g., dependencies of a missing reference).

        2. **Local trace** (*file_paths*): any missing file from
           the trace that wasn't already covered by the manifest
           is reported as a warning (can't download without a hash).

        Args:
            file_paths: Absolute paths from the scene trace.
            scene_hash: XXH128 hex digest of the scene file (for
                manifest matching).
            scene_path: Absolute path of the scene file (for
                deriving the asset root from manifest entries).

        Returns:
            A :class:`SyncPlan` with ``needs_download`` populated.
        """
        needs_download = []
        already_local = []
        download_size = 0
        total_size = 0
        seen_paths = set()  # resolved absolute paths

        # 1. Manifest-based: find the right manifest and check all
        #    its files against the local filesystem.
        if scene_hash:
            result = self.find_manifest_for_scene(scene_hash)
            if result:
                _asset_root_meta, manifest = result

                # Derive the local asset root by matching the scene
                # file's absolute path against its relative manifest
                # entry.  E.g., scene_path=/a/b/v1/shot.ma and
                # manifest entry="v1/shot.ma" → root=/a/b/
                asset_root = None
                if scene_path:
                    scene_resolved = scene_path.resolve()
                    scene_str = str(scene_resolved)
                    for entry in manifest.paths:
                        if scene_str.endswith(entry.path):
                            asset_root = Path(scene_str[: -len(entry.path)])
                            logger.info("Derived asset root: %s", asset_root)
                            break

                for entry in manifest.paths:
                    if asset_root:
                        abs_path = (asset_root / entry.path).resolve()
                    else:
                        abs_path = Path(entry.path)
                    resolved = str(abs_path)
                    seen_paths.add(resolved)

                    if abs_path.exists():
                        already_local.append(
                            SyncFileEntry(
                                path=resolved,
                                size=entry.size,
                                hash=entry.hash,
                            )
                        )
                    else:
                        needs_download.append(
                            SyncFileEntry(
                                path=resolved,
                                size=entry.size,
                                hash=entry.hash,
                            )
                        )
                        download_size += entry.size
                    total_size += entry.size
            else:
                logger.warning(
                    "No manifest found for scene hash %s — "
                    "download will be limited to locally traceable files",
                    scene_hash,
                )

        # 2. Trace-based: pick up any missing files the tracer found
        #    that weren't in the manifest (e.g., scene was modified
        #    after upload, or no manifest matched).
        for fp in file_paths:
            resolved = str(fp.resolve())
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)

            if fp.exists():
                already_local.append(
                    SyncFileEntry(path=resolved, size=0, hash="")
                )
            else:
                logger.warning(
                    "Missing file not in any manifest (no hash, "
                    "cannot download): %s",
                    fp,
                )

        logger.info(
            "Download check: %d need download (%s bytes), %d already local",
            len(needs_download),
            f"{download_size:,}",
            len(already_local),
        )

        return SyncPlan(
            needs_upload=[],
            already_synced=already_local,
            needs_download=needs_download,
            total_files=len(file_paths),
            total_size_bytes=total_size,
            download_size_bytes=download_size,
            _s3_bucket=self._s3_settings.s3BucketName,
            _root_prefix=self._s3_settings.rootPrefix,
            _cache_directory=str(get_cache_directory()),
        )

    # -- Download --------------------------------------------------------

    def download_files(
        self,
        plan: SyncPlan,
        on_progress: Optional[Callable[[ProgressInfo], bool]] = None,
    ) -> DownloadResult:
        """Download files from S3 CAS that are in ``plan.needs_download``.

        Uses the SDK's ``download_files_from_manifests()`` with a
        synthetic manifest built from the plan entries.

        Args:
            plan: A :class:`SyncPlan` from :meth:`prepare_download`.
            on_progress: Optional callback receiving
                :class:`ProgressInfo` snapshots.  Return *False* to
                cancel.

        Returns:
            A :class:`DownloadResult` with summary statistics.
        """
        if not plan.needs_download:
            logger.info("Nothing to download — all files already local.")
            return DownloadResult(
                downloaded_files=0,
                downloaded_bytes=0,
                skipped_files=len(plan.already_synced),
                skipped_bytes=0,
                total_time=0.0,
                transfer_rate=0.0,
            )

        logger.info(
            "Downloading %d file(s) (%s bytes)...",
            len(plan.needs_download),
            f"{plan.download_size_bytes:,}",
        )

        # Build a synthetic manifest for download_files_from_manifests().
        # Group files by their parent directory (download root).
        from deadline.job_attachments.asset_manifests.hash_algorithms import (
            HashAlgorithm,
        )
        from deadline.job_attachments.asset_manifests.v2023_03_03 import (
            asset_manifest as manifest_mod,
        )
        from deadline.job_attachments.download import (
            download_files_from_manifests,
        )
        from deadline.job_attachments.models import FileConflictResolution

        roots = {}  # root_dir → list of ManifestPath
        for entry in plan.needs_download:
            fp = Path(entry.path)
            root = str(fp.parent)
            if root not in roots:
                roots[root] = []
            roots[root].append(
                manifest_mod.ManifestPath(
                    path=fp.name,
                    hash=entry.hash,
                    size=entry.size,
                    mtime=0,
                )
            )

        manifests_by_root = {}
        for root, paths in roots.items():
            manifests_by_root[root] = manifest_mod.AssetManifest(
                hash_alg=HashAlgorithm.XXH128,
                paths=paths,
                total_size=sum(p.size for p in paths),
            )

        cas_prefix = f"{plan._root_prefix}/Data"

        sdk_callback = None
        if on_progress is not None:

            def sdk_callback(metadata):
                info = ProgressInfo(
                    progress=metadata.progress,
                    message=metadata.progressMessage,
                    processed_files=metadata.processedFiles,
                    transfer_rate=metadata.transferRate,
                )
                return on_progress(info)

        stats = download_files_from_manifests(
            s3_bucket=plan._s3_bucket,
            manifests_by_root=manifests_by_root,
            cas_prefix=cas_prefix,
            session=self._queue_session,
            on_downloading_files=sdk_callback,
            conflict_resolution=FileConflictResolution.OVERWRITE,
        )

        logger.info(
            "Download complete: %d file(s), %s bytes in %.1fs",
            stats.processed_files,
            f"{stats.processed_bytes:,}",
            stats.total_time,
        )

        return DownloadResult(
            downloaded_files=stats.processed_files,
            downloaded_bytes=stats.processed_bytes,
            skipped_files=stats.skipped_files,
            skipped_bytes=stats.skipped_bytes,
            total_time=stats.total_time,
            transfer_rate=stats.transfer_rate,
        )
