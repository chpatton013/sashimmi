from ._internal import SubcommandBaseWithWorkspace, register_subcommand
from ..models.reference import Reference


def _print_package(package):
    targets = package.targets
    if targets:
        print("{reference}".format(reference=package.reference))
        for target_reference in package.targets.keys():
            print("  :{target}".format(target=target_reference.target_name))
    else:
        print(
            "{reference} - No targets found".format(
                reference=package.reference
            )
        )


class PackageSubcommand(SubcommandBaseWithWorkspace):
    def name(self):
        return "package"

    def help(self):
        return "Print the targets defined in these packages."

    def configure_subparser(self, subparser):
        subparser.add_argument(
            "reference",
            help="References of the packages within the workspace."
        )

    def run(self, args, workspace):
        reference = Reference.make(args.reference, workspace.root)
        if reference.target_name:
            raise ValueError(
                "Reference {reference} contains a target name".format(
                    reference=reference
                )
            )

        packages = [package for package in workspace.find_packages(reference)]
        if packages:
            for package in packages:
                _print_package(package)
        else:
            print("No packages found in workspace")


register_subcommand(PackageSubcommand())
