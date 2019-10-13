from ._internal import (
    SubcommandBaseWithWorkspace,
    register_subcommand,
    ensure_bin_node,
)
from ..models.shim import read_shims_node, bind_shims


class BindSubcommand(SubcommandBaseWithWorkspace):
    def name(self):
        return "bind"

    def help(self):
        return "Bind all shims."

    def configure_subparser(self, subparser):
        pass

    def run(self, args, workspace):
        ensure_bin_node(workspace.root)
        shims = read_shims_node(workspace.root)
        bind_shims(workspace.root, shims)


register_subcommand(BindSubcommand())
