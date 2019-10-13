from ..component import CommandComponent, DockerComponent
from .reference import Reference


class Target:
    @staticmethod
    def make(package_reference, yaml_node):
        if "name" not in yaml_node:
            raise KeyError(
                "Target in package {package} is missing required attriute 'name'"
                .format(package_reference)
            )
        target_reference = Reference(
            package_reference.package_path, yaml_node["name"]
        )

        components = []

        if DockerComponent.yaml_key() in yaml_node:
            components.append(
                DockerComponent.make_from_yaml_node(
                    yaml_node[DockerComponent.yaml_key()], target_reference
                )
            )

        if CommandComponent.yaml_key() in yaml_node:
            components.append(
                CommandComponent.make_from_yaml_node(
                    yaml_node[CommandComponent.yaml_key()], target_reference
                )
            )

        if len(components) == 0:
            raise KeyError(
                "Target {target} is missing components".
                format(target_reference)
            )

        return Target(None, target_reference, components)

    def __init__(self, package, reference, components):
        self.package = package
        self.reference = reference
        self.components = components

    def __str__(self):
        return "Target({name})".format(name=self.name)

    @property
    def name(self):
        return self.reference.target_name

    @property
    def workspace(self):
        return self.package.workspace

    def command_line_arguments(self):
        arguments = []
        for component in self.components:
            arguments += component.command_line_arguments()
        return arguments

    def environment_variables(self):
        variables = {}
        for component in self.components:
            variables.update(component.environment_variables())
        return variables
