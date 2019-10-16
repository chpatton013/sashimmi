from ._internal import Action, register_action_class


def _substitute_workspace(target):
    return target.workspace.root


def _substitute_package(target):
    return target.package.absolute_path


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

    def substitutions(self, existing_substitutions):
        new_substitutions = existing_substitutions.copy()
        new_substitutions.update({
            "workspace": _substitute_workspace,
            "wks": _substitute_workspace,
            "w": _substitute_workspace,
            "package": _substitute_package,
            "pkg": _substitute_package,
            "p": _substitute_package,
        })
        return new_substitutions


register_action_class(CommandAction)
