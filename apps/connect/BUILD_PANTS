python_requirements(name="reqs", source="requirements.txt")
python_sources(
    name="connect_app",
    sources=["**/*.py"],
)
resource(name="README", source="README.md")

python_distribution(
    name="ftrack_connect",
    dependencies=[
        ":reqs",
        ":connect_app",
        ":README",
        "apps/connect/resource:style"
        # Dependencies on code to be packaged into the distribution.
    ],
    provides=python_artifact(
        name="ftrack_connect",
    ),
    wheel_config_settings={
        "--global-option": ["--python-tag", "py37.py38.py39"]
    },
    generate_setup=False,
)
