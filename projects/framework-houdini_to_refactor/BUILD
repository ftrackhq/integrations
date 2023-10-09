python_sources(
    name="houdini_project",
    sources=["**/*.py"],
    dependencies=[
        "projects/framework-houdini/resource/definitions:definitions"
    ],
)
resource(name="README", source="README.md")

python_distribution(
    name="ftrack_framework_houdini",
    dependencies=[":houdini_project", ":README"],
    provides=python_artifact(
        name="ftrack_framework_houdini",
    ),
    wheel_config_settings={
        "--global-option": ["--python-tag", "py37.py38.py39"]
    },
    generate_setup=False,
)
