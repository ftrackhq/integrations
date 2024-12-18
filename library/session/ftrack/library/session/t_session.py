# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from ftrack.library.authenticate.util.identifier import (
    generate_vault_identifier,
)
from ftrack.library.authenticate.helper.credential import CredentialFactory
from ftrack.library.session.session import SessionProvider
from typing import Optional

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO)

# Test variables (replace with real or mock values for testing)
TEST_URL: str = "https://ftrack-integrations.ftrackapp.com"  # Mock authentication server URL
CREDENTIAL_IDENTIFIER: str = generate_vault_identifier(TEST_URL)


def main() -> None:
    """
    Main function to test the session provider and credential handling.
    """
    # Step 1: Test Credential Provider
    logging.info("Starting credential provider helper...")
    credential_provider = CredentialFactory(CREDENTIAL_IDENTIFIER)

    # Step 2: Test Session Loading
    logging.info("Loading session...")
    session_provider = SessionProvider(credential_provider)
    session: Optional[
        object
    ] = session_provider.new_session_from_stored_credentials(
        spawn_event_hub_thread=True
    )

    if session:
        print(f"Session Loaded: {session}")
    else:
        print("No session loaded. Please check your credential.")


if __name__ == "__main__":
    main()
