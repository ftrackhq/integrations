python_sources(
    name="connect_action_launcher_widget_project",
    sources=["**/*.py"],
)

python_requirements(
    name="reqs",
)

resource(name="README", source="README.md")


python_distribution(
    name="ftrack_connect_action_launcher_widget",
    dependencies=[
        ":reqs",
        ":connect_action_launcher_widget_project",
        ":README",
    ],
    provides=python_artifact(
        name="ftrack_connect_action_launcher_widget",
    ),
    wheel_config_settings={
        "--global-option": ["--python-tag", "py37.py38.py39"]
    },
    generate_setup=False,
)
