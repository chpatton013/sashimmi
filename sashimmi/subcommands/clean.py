from .subcommand import SubcommandBaseWithWorkspace, register_subcommand
from ..models.shim import write_shims_node, bind_shims


class CleanSubcommand(SubcommandBaseWithWorkspace):
    def name(self):
        return "clean"

    def help(self):
        return "Uninstall all shims."

    def configure_subparser(self, subparser):
        pass

    def run(self, args, workspace):
        write_shims_node(workspace.root, {})
        bind_shims(workspace.root, {})


register_subcommand(CleanSubcommand())
