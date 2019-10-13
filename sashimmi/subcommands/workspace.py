from ._internal import SubcommandBaseWithWorkspace, register_subcommand


class WorkspaceSubcommand(SubcommandBaseWithWorkspace):
    def name(self):
        return "workspace"

    def help(self):
        return "Print the packages found in this workspace."

    def configure_subparser(self, subparser):
        pass

    def run(self, args, workspace):
        packages = workspace.packages.keys()
        if packages:
            print("Packages")
            for package_reference in packages:
                print("  {reference}".format(reference=package_reference))
        else:
            print("No packages found in workspace")


register_subcommand(WorkspaceSubcommand())
