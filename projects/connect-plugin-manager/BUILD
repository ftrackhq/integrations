python_sources(
    name="connect_plugin_manager_project",
    sources=["**/*.py"]
)
resource(
    name="README",
    source="README.md"
)


python_distribution(
    name="ftrack_connect_plugin_manager",
    dependencies=[
         ":connect_plugin_manager_project",
         ":README"
    ],
    provides=python_artifact(
        name="ftrack_connect_plugin_manager",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)