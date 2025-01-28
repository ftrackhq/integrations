Connect 4 is designed to be plugable by tools published as python packages.
Our Integrations monorepo consists in the following main folders: Tool, Library and Configuration.
Tool:
- Connect: The main tool that contains CLI commands like install and uv.
- Authenticator: Contains CLI commands to authenticate with the ftrack server.
- Session: Contains CLI commands to manage ftrack sessions.
- Launcher: Contains CLI commands to launch applications based on configurations.
Library:
- Authenticate: Contains the logic to authenticate with the ftrack server.
- Session: Contains the logic to manage ftrack sessions.
- Launch: Contains the logic to launch applications based on configurations.
- Configuration: Contains the logic to manage configurations.
- Utility: Contains utility functions.
Configuration:
- runtime: Contains the runtime configurations.
- maya: Contains the maya specific configurations.