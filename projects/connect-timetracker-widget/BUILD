python_sources(
    name="connect_timetracker_widget_project",
    sources=["**/*.py"],
)
python_requirements(
    name="reqs",
)

resource(name="README", source="README.md")


python_distribution(
    name="ftrack_connect_timetracker_widget",
    dependencies=[":reqs", ":connect_timetracker_widget_project", ":README"],
    provides=python_artifact(
        name="ftrack_connect_timetracker_widget",
    ),
    wheel_config_settings={
        "--global-option": ["--python-tag", "py37.py38.py39"]
    },
    generate_setup=False,
)
