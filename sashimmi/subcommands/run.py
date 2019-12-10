import os

from .subcommand import SubcommandBaseWithWorkspaceReadLock, register_subcommand
from ..models.reference import Reference


class RunSubcommand(SubcommandBaseWithWorkspaceReadLock):
    def name(self):
        return "run"

    def help(self):
        return "Run the command this target maps to in this repository."

    def configure_subparser(self, subparser):
        subparser.add_argument(
            "reference",
            help="Reference of the target which maps to a command."
        )
        subparser.add_argument(
            "arguments", nargs="*", help="Arguments to pass to command"
        )

    def run_with_lock(self, args, workspace, lock):
        reference = Reference.make(args.reference, workspace.root)
        if not reference.target_name:
            raise ValueError(
                "Reference argument {argument} does not contain a target name".
                format(argument=reference)
            )

        targets = list(workspace.find_targets(reference))
        if len(targets) > 1:
            raise ValueError(
                "Reference argument {argument} produces multiple targets".
                format(argument=reference)
            )
        target = targets[0]

        arguments, variables = target.adapt(apply_substitutions=True)
        if not arguments:
            raise ValueError(
                "Target {reference} produces no command line".format(
                    reference=target.reference
                )
            )

        environment = os.environ.copy()
        environment.update(variables)

        os.execvpe(arguments[0], arguments, environment)


register_subcommand(RunSubcommand())
