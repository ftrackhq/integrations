# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Tier-2 test: the standalone process shuts down when Harmony exits.

Its own module so killing Harmony is isolated from the other tier-2
tests (each module gets its own Harmony + standalone via the
module-scoped fixtures). Requires ftrack credentials (the standalone
process must fully bootstrap) - skipped without them.
"""

import time

import pytest

from dcc_test_harness.connect_launcher import resolve_ftrack_credentials

from conftest import tail_file

pytestmark = pytest.mark.skipif(
    resolve_ftrack_credentials() is None,
    reason=(
        "ftrack credentials required: set FTRACK_SERVER and "
        "FTRACK_API_KEY, or log in via ftrack Connect"
    ),
)


def test_standalone_exits_when_harmony_closes(standalone_bundle):
    """Killing Harmony must terminate the standalone helper process.

    Covers the process-cleanup watchdog (and the TCP disconnect fast
    path). Previously the helper lingered after Harmony closed.
    """
    bundle = standalone_bundle
    assert bundle.process.poll() is None, "Standalone not running at start"

    # Simulate Harmony closing.
    bundle.harmony_process.terminate()

    # The watchdog polls every 5s; allow generous margin.
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        if bundle.process.poll() is not None:
            break
        time.sleep(1.0)

    assert bundle.process.poll() is not None, (
        "Standalone process did not exit after Harmony closed.\n"
        f"--- standalone output tail ---\n{tail_file(bundle.log_path)}"
    )
