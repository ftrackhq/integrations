python_sources(
    name="rv_project",
    sources=["**/*.py"],
    dependencies=["projects/rv/resource/plugin:plugin"],
)
resource(name="README", source="README.md")


python_distribution(
    name="ftrack_rv",
    dependencies=[":rv_project", ":README"],
    provides=python_artifact(
        name="ftrack_rv",
    ),
    wheel_config_settings={
        "--global-option": ["--python-tag", "py37.py38.py39"]
    },
    generate_setup=False,
)
