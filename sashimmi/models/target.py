from ..actions import get_action_class
from ..actions.arguments import ArgumentsAction
from ..adapters.exec import ExecAdapter
from .reference import Reference


def _make_actions_from_yaml_node(yaml_node, target_reference):
    actions = []
    for action_yaml_node in yaml_node:
        if "action" not in action_yaml_node:
            raise KeyError(
                "Action in target {target} is missing required attribute 'action'"
                .format(target_reference)
            )
        action_class = get_action_class(action_yaml_node["action"])
        actions.append(
            action_class.make_from_yaml_node(
                action_yaml_node, target_reference
            )
        )
    return actions


def _make_adapters(actions):
    adapters = [ExecAdapter()]
    for action in actions:
        active_adapter = adapters[-1]
        active_adapter.adapt(action)
        next_adapter = action.adapter()
        if next_adapter:
            adapters.append(next_adapter)
    return adapters


class Target:
    @staticmethod
    def make(package_reference, yaml_node):
        if "name" not in yaml_node:
            raise KeyError(
                "Target in package {package} is missing required attribute 'name'"
                .format(package_reference)
            )
        target_name = yaml_node["name"]
        target_reference = Reference(
            package_reference.package_path,
            target_name,
        )

        if "actions" not in yaml_node:
            raise KeyError(
                "Target {target} is missing required attribute 'actions'".
                format(target_reference)
            )
        if not yaml_node["actions"]:
            raise KeyError(
                "Target {target} is missing actions".format(target_reference)
            )
        actions = _make_actions_from_yaml_node(
            yaml_node["actions"],
            target_reference,
        )

        return Target(None, target_reference, actions)

    def __init__(self, package, reference, actions):
        self.package = package
        self.reference = reference
        self.actions = actions

    def __str__(self):
        return "Target({name})".format(name=self.name)

    @property
    def name(self):
        return self.reference.target_name

    @property
    def workspace(self):
        return self.package.workspace

    def adapt(self, arguments=[], apply_substitutions=False):
        adapters = list(
            _make_adapters(self.actions + [ArgumentsAction(arguments)])
        )

        arguments = []
        for adapter in adapters:
            arguments += adapter.command_line_arguments(
                self,
                apply_substitutions=apply_substitutions,
            )

        variables = {}
        for adapter in adapters:
            variables.update(
                adapter.environment_variables(
                    self,
                    apply_substitutions=apply_substitutions,
                )
            )

        return arguments, variables
