from .subcommand import SubcommandBaseWithWorkspaceWriteLock, register_subcommand
from ..models.shim import write_shims_node, bind_shims


class CleanSubcommand(SubcommandBaseWithWorkspaceWriteLock):
    def name(self):
        return "clean"

    def help(self):
        return "Uninstall all shims."

    def configure_subparser(self, subparser):
        subparser.add_argument(
            "--multi",
            action="store_true",
            default=False,
            help="Bind shims in multi-namespace."
        )

    def run_with_lock(self, args, workspace, lock):
        write_shims_node(workspace.root, {})
        bind_shims(
            workspace.root, {},
            self.make_multi_lock() if args.multi else None
        )


register_subcommand(CleanSubcommand())
