from ._internal import Action, register_action_class


class CommandAction(Action):
    @staticmethod
    def name():
        return "command"

    @staticmethod
    def make_from_yaml_node(yaml_node, target_reference):
        if "executable" not in yaml_node:
            raise KeyError(
                "Command component in target {target} is missing required attriute 'executable'"
                .format(target_reference)
            )
        return CommandAction(
            yaml_node["executable"],
            arguments=yaml_node.get("arguments"),
            variables=yaml_node.get("variables")
        )

    def __init__(self, executable, arguments=None, variables=None):
        self.executable = executable
        self.arguments = arguments if arguments else []
        self.variables = variables if variables else {}

    def adapter(self):
        return None

    def command_line_arguments(self):
        return [self.executable] + self.arguments

    def environment_variables(self):
        return self.variables


register_action_class(CommandAction)
