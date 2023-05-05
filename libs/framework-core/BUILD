python_sources(
    name="lib",
    sources=["**/*.py"]
)

python_distribution(
    name="framework_core",
    dependencies=[
         ":lib",
        # Dependencies on code to be packaged into the distribution.
    ],
    provides=python_artifact(
        name="framework_core",
        version="2.21.0",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)