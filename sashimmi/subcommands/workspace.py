from .subcommand import SubcommandBaseWithWorkspaceReadLock, register_subcommand


class WorkspaceSubcommand(SubcommandBaseWithWorkspaceReadLock):
    def name(self):
        return "workspace"

    def help(self):
        return "Print the packages found in this workspace."

    def configure_subparser(self, subparser):
        pass

    def run_with_lock(self, args, workspace, lock):
        packages = workspace.packages.keys()
        if packages:
            print("Packages")
            for package_reference in packages:
                print("  {reference}".format(reference=package_reference))
        else:
            print("No packages found in workspace")


register_subcommand(WorkspaceSubcommand())
