# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

import logging

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

from ftrack_utils.session.ftrack_api_session import get_event_hub_thread


logger = logging.getLogger(__name__)


# Bounded wait for ftrack-api's EventHubThread.wait() to return after
# the hub is disconnected. Without library-level daemonization of that
# thread, this is what keeps Nuke / Maya / etc. from hanging on quit
# if event_hub.wait() doesn't promptly notice the disconnect.
_JOIN_TIMEOUT_SECONDS = 2.0


def connect_event_manager_shutdown(event_manager):
    """Hook a clean-shutdown handler to ``QApplication.aboutToQuit``.

    Closes the ftrack ``event_manager`` (which disconnects the event
    hub and closes the ftrack-api session) when the host DCC quits,
    so the ``EventHubThread``'s blocking ``event_hub.wait()`` returns
    and the interpreter can exit instead of hanging. The hub thread is
    then joined with a bounded timeout; if it stays alive past that we
    log and let the process exit anyway (the OS reaps the thread).

    Safe to call from any DCC's bootstrap once Qt is up; a no-op if no
    ``QApplication`` exists yet (caller's responsibility to invoke
    after Qt init — typical of every ``bootstrap_integration`` entry
    point we have today).
    """
    qapp = QtWidgets.QApplication.instance()
    if qapp is None:
        logger.debug(
            "connect_event_manager_shutdown: no QApplication; skipping"
        )
        return

    def _on_about_to_quit():
        logger.debug("aboutToQuit: closing ftrack event manager")
        try:
            event_manager.close()
        except Exception:
            logger.exception("error closing event manager")
        try:
            thread = get_event_hub_thread(event_manager.session)
        except Exception:
            thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=_JOIN_TIMEOUT_SECONDS)
            if thread.is_alive():
                logger.warning(
                    "EventHubThread still alive after %.1fs join; "
                    "letting process exit",
                    _JOIN_TIMEOUT_SECONDS,
                )

    qapp.aboutToQuit.connect(_on_about_to_quit)
