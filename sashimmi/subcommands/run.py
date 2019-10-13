import os

from ._internal import SubcommandBaseWithWorkspace, register_subcommand
from ..models.reference import Reference


class RunSubcommand(SubcommandBaseWithWorkspace):
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

    def run(self, args, workspace):
        reference = Reference.make(args.reference, workspace.root)
        if not reference.target_name:
            raise ValueError(
                "Reference argument {argument} does not contain a target name".
                format(argument=reference)
            )

        targets = [target for target in workspace.find_targets(reference)]
        if len(targets) > 1:
            raise ValueError(
                "Reference argument {argument} produces multiple targets".
                format(argument=reference)
            )
        target = targets[0]

        command_line = target.command_line_arguments() + args.arguments
        if not command_line:
            raise ValueError(
                "Target {reference} produces no command line".format(
                    reference=target.reference
                )
            )

        environment = os.environ.copy()
        environment.update(target.environment_variables())

        os.execvpe(command_line[0], command_line, environment)


register_subcommand(RunSubcommand())
