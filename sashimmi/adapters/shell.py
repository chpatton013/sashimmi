from ._internal import Adapter


class ShellAdapter(Adapter):
    def __init__(self):
        super(ShellAdapter, self).__init__()

    def command_line_arguments(self):
        cmd_line_args = []
        for action in self.actions:
            cmd_line_args += action.command_line_arguments()

        env_var_args = []
        for action in self.actions:
            for key, value in action.environment_variables().items():
                env_var_args.append(
                    "{key}={value}".format(key=key, value=value)
                )

        if env_var_args:
            return ["sh", "-c", " ".join(env_var_args + cmd_line_args)]
        else:
            return cmd_line_args

    def environment_variables(self):
        return {}
