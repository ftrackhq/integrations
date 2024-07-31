import argparse
import inspect
import importlib.util
import os
import sys


# TODO: somehow parser values of the arguments that contain python clases for when users want to override a manager


def _import_class_from_file(file_path, class_name):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def _get_builder_args(builder_class):
    # Extract the __init__ method signature and read the docstring
    init_signature = inspect.signature(builder_class.__init__)
    doc = builder_class.__init__.__doc__ or ''
    doc_lines = doc.splitlines()
    doc_dict = {}
    for line in doc_lines:
        if ':param ' in line:
            parts = line.split(':param ')[1].split(': ')
            if len(parts) == 2:
                param_name, param_desc = parts
                doc_dict[param_name.strip()] = param_desc.strip()
    # Exclude 'self' and collect other parameters
    return [
        (
            param.name,
            param.annotation,
            param.default,
            doc_dict.get(param.name, 'No description'),
        )
        for param in init_signature.parameters.values()
        if param.name != 'self'
    ]


def parse_extra_args(unknown_args):
    kwargs = {}
    it = iter(unknown_args)
    for arg in it:
        if arg.startswith('--'):
            key = arg.lstrip('--')
            try:
                value = next(it)
                if value.startswith('--'):
                    raise ValueError(
                        f"Expected value after {key}, but got another argument: {value}"
                    )
            except StopIteration:
                value = None  # Handle flags without values
            kwargs[key] = value
    return kwargs


def main():
    # First, check if --help is present

    if '--help' and '--builder' in sys.argv:
        parser = argparse.ArgumentParser(
            description='BuildTool', add_help=False
        )
    else:
        parser = argparse.ArgumentParser(description='BuildTool')
    parser.add_argument(
        '--builder',
        required=True,
        help='Specify the builder to use (file path and class name, e.g., path/to/file.py:ClassName)',
    )
    parser.add_argument(
        '--source_module', required=True, help='Specify the source module path'
    )

    args, unknown_args = parser.parse_known_args()

    file_path = None
    class_name = None
    builder_class = None

    try:
        file_path, class_name = args.builder.split(':')
    except ValueError:
        parser.error(
            "The --builder argument must be in the form 'path/to/file.py:ClassName'"
        )

    if not os.path.isfile(file_path):
        parser.error(f"File '{file_path}' does not exist.")

    try:
        builder_class = _import_class_from_file(file_path, class_name)
    except (ModuleNotFoundError, AttributeError) as e:
        parser.error(f"Error loading builder class '{args.builder}': {e}")

    if '--help' in unknown_args:
        # Show help for the specific builder
        builder_args = _get_builder_args(builder_class)
        print(f"Usage: {parser.prog} --builder {args.builder} [options]")
        print("\nOptions:")
        for arg_name, arg_type, arg_default, arg_desc in builder_args:
            default_str = (
                f' [default: {arg_default.__name__ if isinstance(arg_default, type) else arg_default}]'
                if arg_default != inspect.Parameter.empty
                else ''
            )
            print(
                f"  --{arg_name} \t {arg_desc} (type: {arg_type.__name__ if arg_type != inspect.Parameter.empty else 'unknown'}){default_str}"
            )
        return

    # Parse unknown arguments and add the source_module into them
    builder_args = parse_extra_args(unknown_args)
    builder_args['source_module'] = args.source_module

    print(f"Building with {builder_args}...")

    builder = builder_class(**builder_args)
    builder.build()
