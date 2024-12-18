# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from ftrack.library.authenticate.authenticate import Authenticate
from ftrack.library.authenticate.util.identifier import (
    generate_vault_identifier,
)
from ftrack.library.authenticate.helper.credential import CredentialFactory
from ftrack.library.authenticate.helper.webserver import WebServerFactory

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO)

# Test variables (replace with real or mock values for testing)
TEST_URL = "https://ftrack-integrations.ftrackapp.com"  # Mock authentication server URL
CREDENTIAL_IDENTIFIER = generate_vault_identifier(TEST_URL)


def main() -> None:
    # Step 1: Test Authentication
    logging.info("Starting authentication...")
    auth = Authenticate(
        server_url=TEST_URL,
        credential_factory=CredentialFactory(CREDENTIAL_IDENTIFIER),
        web_server_factory=WebServerFactory(),
    )
    auth.authenticate_browser()


if __name__ == "__main__":
    main()
