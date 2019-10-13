from ._internal import Adapter


class ExecAdapter(Adapter):
    def __init__(self):
        super(ExecAdapter, self).__init__()

    def command_line_arguments(self):
        arguments = []
        for action in self.actions:
            arguments += action.command_line_arguments()
        return arguments

    def environment_variables(self):
        variables = {}
        for action in self.actions:
            variables.update(action.environment_variables())
        return variables
