python_sources(
    name="nuke_project",
    sources=["**/*.py"],
    dependencies=["projects/framework-nuke/resource/definitions:definitions"],
)
resource(name="README", source="README.md")


python_distribution(
    name="ftrack_framework_nuke",
    dependencies=[":nuke_project", ":README"],
    provides=python_artifact(
        name="ftrack_framework_nuke",
    ),
    wheel_config_settings={
        "--global-option": ["--python-tag", "py37.py38.py39"]
    },
    generate_setup=False,
)
