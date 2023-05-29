python_sources(
    name="application_launcher_project",
    sources=["**/*.py"],
    dependencies=["projects/application-launcher/resource/config:config"]
)
resource(
    name="README",
    source="README.md"
)


python_distribution(
    name="ftrack_application_launcher",
    dependencies=[
         ":application_launcher_project",
         ":README"
    ],
    provides=python_artifact(
        name="ftrack_application_launcher",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)