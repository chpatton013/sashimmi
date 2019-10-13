from ._internal import Action


class ArgumentsAction(Action):
    @staticmethod
    def name():
        return None

    @staticmethod
    def make_from_yaml_node(yaml_node, target_reference):
        return None

    def __init__(self, arguments):
        self.arguments = arguments

    def adapter(self):
        return None

    def command_line_arguments(self):
        return self.arguments

    def environment_variables(self):
        return {}
