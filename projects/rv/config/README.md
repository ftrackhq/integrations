# Configuration Examples

This directory contains example configuration files for setting up the ftrack RV integration.

## macOS Environment Variables (LaunchAgent)

**File:** `macos/com.ftrack.rv.plist`

This example LaunchAgent configuration file allows macOS GUI applications (like RV launched from Finder or Dock) to access ftrack environment variables system-wide.

### Installation

1. Copy the example file:
   ```bash
   cp config/macos/com.ftrack.rv.plist ~/Library/LaunchAgents/com.ftrack.rv.plist
   ```

2. Edit the file with your actual ftrack credentials:
   ```bash
   nano ~/Library/LaunchAgents/com.ftrack.rv.plist
   ```
   
   Replace the following values:
   - `https://yourcompany.ftrackapp.com` → Your ftrack server URL
   - `your_username` → Your ftrack username or API user
   - `your_api_key` → Your ftrack API key

3. Load the configuration:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.ftrack.rv.plist
   ```

4. Verify it's loaded:
   ```bash
   launchctl list | grep ftrack
   ```

5. Log out and log back in, or restart any running applications

### Updating Credentials

To update your credentials:

```bash
# Unload the current configuration
launchctl unload ~/Library/LaunchAgents/com.ftrack.rv.plist

# Edit the file
nano ~/Library/LaunchAgents/com.ftrack.rv.plist

# Reload the configuration
launchctl load ~/Library/LaunchAgents/com.ftrack.rv.plist
```

### Removing

To remove the LaunchAgent:

```bash
launchctl unload ~/Library/LaunchAgents/com.ftrack.rv.plist
rm ~/Library/LaunchAgents/com.ftrack.rv.plist
```

## Security Note

The plist file contains your ftrack API credentials in plain text. Ensure proper file permissions:

```bash
chmod 600 ~/Library/LaunchAgents/com.ftrack.rv.plist
```

This restricts access to your user account only.
