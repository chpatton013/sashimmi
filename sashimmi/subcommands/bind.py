from .subcommand import SubcommandBaseWithWorkspaceWriteLock, register_subcommand
from ..models.shim import read_shims_node, bind_shims


class BindSubcommand(SubcommandBaseWithWorkspaceWriteLock):
    def name(self):
        return "bind"

    def help(self):
        return "Bind all shims."

    def configure_subparser(self, subparser):
        subparser.add_argument(
            "--multi",
            action="store_true",
            default=False,
            help="Bind shims in multi-namespace."
        )

    def run_with_lock(self, args, workspace, lock):
        shims = read_shims_node(workspace.root)
        bind_shims(
            workspace.root, shims,
            self.make_multi_lock() if args.multi else None
        )


register_subcommand(BindSubcommand())
