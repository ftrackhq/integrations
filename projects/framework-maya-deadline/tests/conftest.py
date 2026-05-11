# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Test configuration for framework-maya-deadline.

Usage::

    pytest tests/ -v \\
        --dcc-connect-plugin ../framework-maya \\
        --dcc-connect-plugin .

The first ``--dcc-connect-plugin`` is the primary
(framework-maya, provides DCC discovery).  The second
layers framework-maya-deadline on top.
"""

import importlib.util
from pathlib import Path

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "deadline_cloud: requires AWS Deadline Cloud credentials",
    )


# ---------------------------------------------------------------------------
# Session-scoped Deadline Cloud fixtures — validated once at startup.
# Any deadline_cloud test that uses these fixtures will fail immediately
# if credentials are expired or no farms/queues exist.
# ---------------------------------------------------------------------------

_wrapper_path = (
    Path(__file__).parent.parent
    / "source"
    / "ftrack_framework_maya_deadline"
    / "wrappers"
    / "deadline.py"
)


def _load_real_wrapper_class():
    """Load the real DeadlineWrapper (no stubs)."""
    spec = importlib.util.spec_from_file_location(
        "deadline_wrapper_real", _wrapper_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DeadlineWrapper


@pytest.fixture(scope="session")
def deadline_wrapper():
    """Session-scoped DeadlineWrapper with fully validated credentials.

    Validates the entire chain: AWS credentials → Deadline Cloud API
    → at least one farm visible.  Fails immediately with a clear
    message if anything is wrong — no false positives.
    """
    DeadlineWrapper = _load_real_wrapper_class()
    wrapper = DeadlineWrapper()

    # 1. Validate AWS credentials.
    try:
        session = wrapper.aws_session
        sts = session.client("sts")
        sts.get_caller_identity()
    except Exception as exc:
        pytest.fail(
            f"Deadline Cloud credentials are not valid. "
            f"Log in via Deadline Cloud Monitor and retry.\n"
            f"Error: {exc}"
        )

    # 2. Validate Deadline Cloud API connectivity.
    try:
        farms = wrapper.list_farms()
    except Exception as exc:
        pytest.fail(
            f"Cannot reach Deadline Cloud API. "
            f"Log in via Deadline Cloud Monitor and retry.\n"
            f"Error: {exc}"
        )

    if not farms:
        pytest.fail(
            "Deadline Cloud credentials are valid but no farms are "
            "visible. Verify your Deadline Cloud Monitor profile "
            "has access to at least one farm."
        )

    return wrapper


@pytest.fixture(scope="session")
def deadline_farm(deadline_wrapper):
    """First available Deadline Cloud farm.

    The ``deadline_wrapper`` fixture already validated that at
    least one farm exists, so this just returns it.
    """
    return deadline_wrapper.list_farms()[0]


@pytest.fixture(scope="session")
def deadline_queue(deadline_wrapper, deadline_farm):
    """First queue in the first farm.

    Fails if no queues exist.
    """
    queues = deadline_wrapper.list_queues(deadline_farm["farmId"])
    if not queues:
        pytest.fail(
            f"No queues in farm {deadline_farm['displayName']!r}. "
            f"Verify your Deadline Cloud Monitor configuration."
        )
    return queues[0]


@pytest.fixture(scope="session")
def deadline_s3_settings(deadline_wrapper, deadline_farm, deadline_queue):
    """``(queue_dict, S3Settings)`` tuple for the first queue.

    Validates that the queue has job attachment settings with an
    S3 bucket and root prefix configured.
    """
    queue, s3_settings = deadline_wrapper.get_queue_settings(
        deadline_farm["farmId"], deadline_queue["queueId"]
    )
    if not getattr(s3_settings, "s3BucketName", None):
        pytest.fail(
            f"Queue {queue.get('displayName')!r} has no S3 bucket "
            f"configured in jobAttachmentSettings."
        )
    return queue, s3_settings
