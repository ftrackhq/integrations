name = "framework_maya"
version = "1.0.0"
requires = ["python-3.10", "pyyaml"]


def commands():
    env.PYTHONPATH.prepend("{root}/python")
    env.PATH.prepend("{root}/bin")
