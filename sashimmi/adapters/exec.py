from ._internal import substitute_list, substitute_dict
from .adapter import Adapter


class ExecAdapter(Adapter):
    def __init__(self):
        super(ExecAdapter, self).__init__()

    def command_line_arguments(self, target, apply_substitutions=False):
        arguments = []
        substitutions = {}
        for action in self.actions:
            substitutions = action.substitutions(substitutions)
            arguments += substitute_list(
                action.command_line_arguments(),
                target,
                substitutions,
                apply_substitutions=apply_substitutions,
            )
        return arguments

    def environment_variables(self, target, apply_substitutions=False):
        variables = {}
        substitutions = {}
        for action in self.actions:
            substitutions = action.substitutions(substitutions)
            variables.update(
                substitute_dict(
                    action.environment_variables(),
                    target,
                    substitutions,
                    apply_substitutions=apply_substitutions,
                )
            )
        return variables
