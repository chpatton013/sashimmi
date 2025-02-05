import logging

from .subcommand import SubcommandBaseWithWorkspaceWriteLock, register_subcommand
from ..models.reference import Reference
from ..models.shim import Shim, read_shims_node, write_shims_node, bind_shims


class InstallSubcommand(SubcommandBaseWithWorkspaceWriteLock):
    def name(self):
        return "install"

    def help(self):
        return "Install shims for these targets."

    def configure_subparser(self, subparser):
        subparser.add_argument(
            "references",
            nargs="+",
            help=
            "References of the targets which map to commands. Targets listed later take precedence."
        )
        subparser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help=
            "Allow targets with conflicting names to override previously-installed shims."
        )
        subparser.add_argument(
            "--multi",
            action="store_true",
            default=False,
            help="Bind shims in multi-namespace."
        )

    def run_with_lock(self, args, workspace, lock):
        target_references = [
            Reference.make(reference, workspace.root)
            for reference in args.references
        ]

        shims = read_shims_node(workspace.root)
        for reference in target_references:
            for target in workspace.find_targets(reference):
                name = target.reference.target_name
                if name in shims:
                    if force:
                        logging.warning(
                            "Overwriting shim '%s' with target '%st}'",
                            name,
                            target.reference,
                        )
                    else:
                        raise ValueError(
                            "Shim '{name}' is already installed".format(
                                name=name
                            )
                        )
                else:
                    logging.info(
                        "Installing shim '%s' with target '%s'",
                        name,
                        target.reference,
                    )
                shims[name] = Shim(name, target.reference)

        write_shims_node(workspace.root, shims)
        bind_shims(
            workspace.root, shims,
            self.make_multi_lock() if args.multi else None
        )


register_subcommand(InstallSubcommand())
