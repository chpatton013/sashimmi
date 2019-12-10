import shlex

from .subcommand import SubcommandBaseWithWorkspaceReadLock, register_subcommand
from ..models.reference import Reference

TARGET_TEMPLATE = """\
  {reference}
    ENVIRONMENT: {environment}
    COMMANDLINE: {command}\
"""


def _print_target(target):
    arguments, variables = target.adapt(apply_substitutions=False)
    environment_variables = [
        "{key}={value}".format(key=key, value=value)
        for key, value in variables.items()
    ]
    print(
        TARGET_TEMPLATE.format(
            reference=target.reference,
            environment=" ".join(environment_variables),
            command=" ".join([shlex.quote(arg) for arg in arguments]),
        )
    )


class TargetSubcommand(SubcommandBaseWithWorkspaceReadLock):
    def name(self):
        return "target"

    def help(self):
        return "Print the commands these targets map to in this repository.<Paste>"

    def configure_subparser(self, subparser):
        subparser.add_argument(
            "references",
            nargs="+",
            help="References of the targets which map to commands."
        )

    def run_with_lock(self, args, workspace, lock):
        references = [
            Reference.make(reference, workspace.root)
            for reference in args.references
        ]
        targets = []
        for reference in references:
            for target in workspace.find_targets(reference):
                targets.append(target)

        if targets:
            print("Targets")
            for target in targets:
                _print_target(target)
        else:
            print("No matching targets defined in workspace")


register_subcommand(TargetSubcommand())
