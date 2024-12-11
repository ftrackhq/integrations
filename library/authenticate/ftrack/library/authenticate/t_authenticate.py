# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from ftrack.library.authenticate.authenticate import Authenticate
from ftrack.library.authenticate.util.identifier import generate_credential_identifier
from ftrack.library.authenticate.helper.credential import CredentialProvider

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO)

# Test variables (replace with real or mock values for testing)
TEST_URL = "https://ftrack-integrations.ftrackapp.com"  # Mock authentication server URL
CREDENTIAL_IDENTIFIER = generate_credential_identifier(TEST_URL)


def main():
    # Step 1: Test Credential Provider
    logging.info("Starting credential provider helper...")
    credential_provider = CredentialProvider(CREDENTIAL_IDENTIFIER)

    # Step 2: Test Authentication
    logging.info("Starting authentication...")
    auth = Authenticate(server_url=TEST_URL, credential_provider=credential_provider)
    auth.browser_authenticate()


if __name__ == "__main__":
    main()
