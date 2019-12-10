from .subcommand import SubcommandBaseWithWorkspaceReadLock, register_subcommand
from ..models.shim import read_shims_node


def _print_shim(name, reference):
    print("  {name}: {reference}".format(name=name, reference=reference))


class ShimsSubcommand(SubcommandBaseWithWorkspaceReadLock):
    def name(self):
        return "shims"

    def help(self):
        return "Print the shims installed in this workspace."

    def configure_subparser(self, subparser):
        pass

    def run_with_lock(self, args, workspace, lock):
        shims = read_shims_node(workspace.root)
        if shims:
            print("Shims")
            for name, target in shims.items():
                _print_shim(name, target.reference)
        else:
            print("No shims installed in workspace")


register_subcommand(ShimsSubcommand())
