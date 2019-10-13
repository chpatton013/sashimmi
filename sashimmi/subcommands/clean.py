from ._internal import (
    SubcommandBaseWithWorkspace,
    register_subcommand,
    ensure_bin_node,
)
from ..models.shim import write_shims_node, bind_shims


class CleanSubcommand(SubcommandBaseWithWorkspace):
    def name(self):
        return "clean"

    def help(self):
        return "Uninstall all shims."

    def configure_subparser(self, subparser):
        pass

    def run(self, args, workspace):
        ensure_bin_node(workspace.root)
        write_shims_node(workspace.root, {})
        bind_shims(workspace.root, {})


register_subcommand(CleanSubcommand())
