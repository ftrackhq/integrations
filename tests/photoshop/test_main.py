import subprocess
import time
import os
import signal
import pytest
import shutil
import dotenv
import contextlib
import ftrack_api
import uuid
import unittest.mock


# Load the .env file
dotenv.load_dotenv('.env')

@contextlib.contextmanager
def javascript_process(integration_session_id):
    environment = os.environ.copy()
    environment["FTRACK_INTEGRATION_SESSION_ID"] = integration_session_id
    process = subprocess.Popen(
        ['npm', 'start'],
        cwd='javascript-environment',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=environment
    )
    time.sleep(1)

    try:
        yield process
    finally:
        os.killpg(process.pid, signal.SIGINT)
        stdout, _ = process.communicate()
        print(stdout)


@pytest.fixture(scope='session', autouse=True)
def setup_and_teardown():

    # npm install packages.
    process = subprocess.Popen(
        ['npm', 'install'],
        cwd='javascript-environment',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    # Print output.
    for line in iter(process.stdout.readline, b''):
        print(line.decode().strip())

    process.wait()

    yield



@pytest.mark.usefixtures("setup_and_teardown")
def test_rpc_call():
    integration_session_id = str(uuid.uuid4())
    session = ftrack_api.Session(auto_connect_event_hub=True)

    mocked_callback = unittest.mock.Mock(return_value=None)

    session.event_hub.subscribe(
        'topic="ftrack.framework.discover.remote.integration"',
        mocked_callback
    )
    time.sleep(2)

    with javascript_process(integration_session_id):
        # Start the javascript process and wait for the event.
        session.event_hub.wait(duration=2)

        assert mocked_callback.call_count == 1
        assert mocked_callback.call_args[0][0]['data']['integration_session_id'] == integration_session_id
