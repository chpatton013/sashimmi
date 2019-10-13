import abc


class Component(metaclass=abc.ABCMeta):
    @staticmethod
    @abc.abstractmethod
    def yaml_key():
        pass

    @staticmethod
    @abc.abstractmethod
    def make_from_yaml_node(yaml_node, target_reference):
        pass

    @abc.abstractmethod
    def command_line_arguments(self):
        pass

    @abc.abstractmethod
    def environment_variables(self):
        pass


class CommandComponent(Component):
    @staticmethod
    def yaml_key():
        return "command"

    @staticmethod
    def make_from_yaml_node(yaml_node, target_reference):
        if "executable" not in yaml_node:
            raise KeyError(
                "Command component in target {target} is missing required attriute 'executable'"
                .format(target_reference)
            )
        return CommandComponent(
            yaml_node["executable"],
            arguments=yaml_node.get("arguments"),
            variables=yaml_node.get("variables")
        )

    def __init__(self, executable, arguments=None, variables=None):
        self.executable = executable
        self.arguments = arguments if arguments else []
        self.variables = variables if variables else {}

    def command_line_arguments(self):
        return [self.executable] + self.arguments

    def environment_variables(self):
        return self.variables


class DockerComponent(Component):
    @staticmethod
    def yaml_key():
        return "docker"

    @staticmethod
    def make_from_yaml_node(yaml_node, target_reference):
        if "image" not in yaml_node:
            raise KeyError(
                "Docker component in target {target} is missing required attriute 'image'"
                .format(target_reference)
            )
        return DockerComponent(
            yaml_node["image"],
            arguments=yaml_node.get("arguments"),
            variables=yaml_node.get("variables")
        )

    def __init__(self, image, arguments=None, variables=None):
        self.image = image
        self.arguments = arguments if arguments else []
        self.variables = variables if variables else {}

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
        return self.variables
