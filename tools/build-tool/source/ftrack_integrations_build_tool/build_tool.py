# The idea is to be able to call the build tool from command line  and pass the desired builder as argument
import argparse


# Command Line Interface
def main():
    parser = argparse.ArgumentParser(description='BuildTool')
    parser.add_argument(
        '--builder', required=True, help='Specify the builder to use'
    )
    parser.add_argument(
        '--source_module', required=True, help='Specify the source module path'
    )
    # parser.add_argument('--file_manager', help='Specify a custom file manager')
    # parser.add_argument('--dependency_manager', help='Specify a custom dependency manager')
    # parser.add_argument('--project_manager', help='Specify a custom project manager')
    parser.add_argument(
        '-- override_managers',
        nargs=argparse.REMAINDER,
        help='Additional keyword arguments',
    )

    args = parser.parse_args()

    builder_class = globals()[args.builder]
    # file_manager_class = globals().get(args.file_manager)
    # dependency_manager_class = globals().get(args.dependency_manager)
    # project_manager_class = globals().get(args.project_manager)

    source_module = args.source_module
    # TODO: We instance them on the builder
    # file_manager = file_manager_class(source_module)
    # dependency_manager = dependency_manager_class(source_module)
    # project_manager = project_manager_class(source_module)

    # source_module,
    # python_environment_path,

    # TODO: find a way to pass all arguments to the builder, and in case something is wrong, then is the builder that will raise the errror.

    builder = builder_class(source_module**kwargs)
    builder.build()


if __name__ == '__main__':
    main()
