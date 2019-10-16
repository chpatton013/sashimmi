from ._internal import Action, register_action_class
from ..adapters.shell import ShellAdapter


class DockerAction(Action):
    @staticmethod
    def name():
        return "docker"

    @staticmethod
    def make_from_yaml_node(yaml_node, target_reference):
        if "image" not in yaml_node:
            raise KeyError(
                "Docker component in target {target} is missing required attriute 'image'"
                .format(target_reference)
            )
        return DockerAction(
            yaml_node["image"],
            arguments=yaml_node.get("arguments"),
            variables=yaml_node.get("variables")
        )

    def __init__(self, image, arguments=None, variables=None):
        self.image = image
        self.arguments = arguments if arguments else []
        self.variables = variables if variables else {}

    def adapter(self):
        return ShellAdapter()

    def command_line_arguments(self):
        command = ["docker", "run"]
        command += [
            "--env={key}={value}".format(key=key, value=value)
            for key, value in self.variables.items()
        ]
        command += self.arguments
        command.append(self.image)
        return command

    def environment_variables(self):
        return {}

    def substitutions(self, existing_substitutions):
        return {}


register_action_class(DockerAction)
