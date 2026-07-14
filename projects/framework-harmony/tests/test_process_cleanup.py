# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Tier-2 tests: the standalone process shuts down when Harmony exits.

Its own module so killing Harmony is isolated from the other tier-2
tests. Uses the function-scoped fixtures so each test gets a fresh
Harmony + standalone (only one Harmony may run at a time, and every test
here kills it). Requires ftrack credentials (the standalone process must
fully bootstrap) - skipped without them.

The standalone is a persistent process that outlives dialogs and scene
switches; it is torn down only by the process watchdog when Harmony goes
away. These tests exercise both exit modes:

- a graceful quit (as a user closing the app), and
- an abrupt crash (SIGKILL, leaving a half-open socket),

and assert the watchdog terminates the standalone in either case.
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

# The watchdog polls every 5s; allow a generous margin.
CLEANUP_DEADLINE_SECONDS = 40


def _assert_standalone_exits(bundle):
    """Poll until the standalone process exits, or fail with its log."""
    deadline = time.monotonic() + CLEANUP_DEADLINE_SECONDS
    while time.monotonic() < deadline:
        if bundle.process.poll() is not None:
            return
        time.sleep(1.0)

    assert bundle.process.poll() is not None, (
        "Standalone process did not exit after Harmony closed.\n"
        f"--- standalone output tail ---\n{tail_file(bundle.log_path)}"
    )


def test_standalone_exits_when_harmony_quits(standalone_bundle_function):
    """A graceful Harmony quit must terminate the standalone helper."""
    bundle = standalone_bundle_function
    assert bundle.process.poll() is None, "Standalone not running at start"

    # Simulate the user quitting Harmony normally.
    bundle.harmony_process.quit()

    _assert_standalone_exits(bundle)


def test_standalone_exits_when_harmony_crashes(standalone_bundle_function):
    """An abrupt Harmony crash must terminate the standalone helper.

    SIGKILL leaves a half-open socket (no clean disconnect), so this
    relies entirely on the process watchdog - the case where the helper
    previously lingered.
    """
    bundle = standalone_bundle_function
    assert bundle.process.poll() is None, "Standalone not running at start"

    # Simulate Harmony crashing (SIGKILL, no graceful shutdown).
    bundle.harmony_process.terminate()

    _assert_standalone_exits(bundle)
