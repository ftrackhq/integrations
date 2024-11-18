name = "framework_maya"

version = "1.0.0"

authors = ["test"]

description = """
    Python-based hello world example package.
    """

tools = ["hello"]

requires = ["python", "source"]

uuid = "examples.framework_maya_py"

build_command = 'python {root}/rez_build.py {install}'


def commands():
    env.PYTHONPATH.append("{root}/source")
    env.PATH.append("{root}/bin")
