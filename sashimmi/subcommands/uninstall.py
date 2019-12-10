import logging

from .subcommand import SubcommandBaseWithWorkspaceWriteLock, register_subcommand
from ..models.reference import Reference
from ..models.shim import read_shims_node, write_shims_node, bind_shims


def _uninstall_shim(target, shims):
    name = target.reference.target_name
    if name in shims:
        logging.info(
            "Uninstalling shim '%s' with target '%s'", name, target.reference
        )
        del shims[name]
    else:
        logging.debug(
            "Skipping missing shim '%s' with target '%s'",
            name,
            target.reference,
        )


class UninstallSubcommand(SubcommandBaseWithWorkspaceWriteLock):
    def name(self):
        return "uninstall"

    def help(self):
        return "Uninstall shims for these targets."

    def configure_subparser(self, subparser):
        subparser.add_argument(
            "references",
            nargs="+",
            help="References of the targets which map to commands."
        )
        subparser.add_argument(
            "--multi",
            action="store_true",
            default=False,
            help="Bind shims in multi-namespace."
        )

    def run_with_lock(self, args, workspace, lock):
        references = [
            Reference.make(reference, workspace.root)
            for reference in args.references
        ]

        shims = read_shims_node(workspace.root)
        for reference in references:
            for target in workspace.find_targets(reference):
                _uninstall_shim(target, shims)

        write_shims_node(workspace.root, shims)
        bind_shims(
            workspace.root, shims,
            self.make_multi_lock() if args.multi else None
        )


register_subcommand(UninstallSubcommand())
