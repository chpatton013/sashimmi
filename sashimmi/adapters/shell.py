from ._internal import Adapter, substitute_list, substitute_dict


class ShellAdapter(Adapter):
    def __init__(self):
        super(ShellAdapter, self).__init__()

    def command_line_arguments(self, target, apply_substitutions=False):
        cmd_line_args = []
        substitutions = {}
        for action in self.actions:
            substitutions = action.substitutions(substitutions)
            cmd_line_args += substitute_list(
                action.command_line_arguments(),
                target,
                substitutions,
                apply_substitutions=apply_substitutions,
            )

        env_var_args = []
        substitutions = {}
        for action in self.actions:
            substitutions = action.substitutions(substitutions)
            variables = substitute_dict(
                action.environment_variables(),
                target,
                substitutions,
                apply_substitutions=apply_substitutions,
            )
            env_var_args += [
                "{key}={value}".format(key=key, value=value)
                for key, value in variables.items()
            ]

        if env_var_args:
            return ["sh", "-c", " ".join(env_var_args + cmd_line_args)]
        else:
            return cmd_line_args

    def environment_variables(self, target, apply_substitutions=False):
        return {}
