# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from ftrack.library.authenticate.authenticate import Authenticate
from ftrack.library.authenticate.session import SessionProvider
from ftrack.library.authenticate.util.identifier import connect_identifier

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO)

# Test variables (replace with real or mock values for testing)
TEST_URL = "https://ftrack-integrations.ftrackapp.com"  # Mock authentication server URL
TEST_IDENTIFIER = connect_identifier()


def main():
    # Step 1: Test Authentication
    logging.info("Starting authentication...")
    auth = Authenticate(server_url=TEST_URL, identifier=TEST_IDENTIFIER)
    auth.browser_authenticate()

    # Step 2: Test Session Loading
    logging.info("Loading session...")
    session_provider = SessionProvider(TEST_IDENTIFIER)
    session = session_provider.load_session()

    if session:
        print(f"Session Loaded: {session}")
    else:
        print("No session loaded. Please check your credential.")


if __name__ == "__main__":
    main()
