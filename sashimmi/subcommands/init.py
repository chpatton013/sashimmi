import logging

from ._internal import ensure_root_node, ensure_workspace, find_root_directory
from .subcommand import SubcommandBase, register_subcommand
from ..constants import root_node
from ..models.shim import write_shims_node, bind_shims


class InitSubcommand(SubcommandBase):
    def name(self):
        return "init"

    def help(self):
        return "Initialize a new sashimmi workspace."

    def configure_subparser(self, subparser):
        subparser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Skip check for existing workspaces."
        )

    def main(self, args):
        if not args.force:
            try:
                workspace = find_root_directory(args.root)
            except RuntimeError:
                pass
            else:
                raise RuntimeError(
                    "Cannot initialize sashimmi workspace in {root} because a workspace already exists in {workspace}"
                    .format(root=args.root, workspace=workspace)
                )

        ensure_root_node(args.root)
        ensure_workspace(args.root)
        write_shims_node(args.root, {})
        bind_shims(args.root, {}, None)
        logging.info(
            "Initialized new sashimmi workspace in %s", root_node(args.root)
        )


register_subcommand(InitSubcommand())
