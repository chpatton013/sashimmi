import os

from ..constants import PACKAGE_WILDCARD_TOKEN, RECURSIVE_WILDCARD_TOKEN
from ._internal import load_yaml_document
from .target import Target
from .reference import Reference
from .validation import validate_target_name_charset


def _validate_package_target_name(name, reference):
    if name in (PACKAGE_WILDCARD_TOKEN, RECURSIVE_WILDCARD_TOKEN):
        raise ValueError(
            "Target name '{name}' in package {package} is reserved".format(
                name=name, package=reference
            )
        )
    validate_target_name_charset(name, reference)


class Package:
    @staticmethod
    def __load_targets(root, reference):
        document = load_yaml_document(
            os.path.join(root, reference.package_node_path)
        )
        names = set()
        for target in document.get("targets", []):
            if "name" not in target:
                raise KeyError(
                    "Target in package {package} is missing required attriute 'name'"
                    .format(package=reference)
                )
            name = target["name"]

            _validate_package_target_name(name, reference)

            if name in names:
                raise ValueError(
                    "Target name '{name}' is duplicated in packge {package}".
                    format(name=name, package=reference)
                )
            names.add(name)

            yield Reference(reference.package_path, name), target

    @staticmethod
    def make(root, package_reference):
        targets = {
            target_reference: Target.make(package_reference, target_yml)
            for target_reference, target_yml in
            Package.__load_targets(root, package_reference)
        }
        return Package(None, package_reference, targets)

    def __init__(self, workspace, reference, targets):
        self.workspace = workspace
        self.reference = reference
        self.targets = targets
        for target in self.targets.values():
            target.package = self

    def __str__(self):
        return "Package({reference})".format(reference=self.reference)

    @property
    def path(self):
        return self.reference.package_path

    @property
    def absolute_path(self):
        return os.path.join(self.workspace.root, self.path)

    @property
    def node(self):
        return self.reference.package_node_path

    @property
    def absolute_node(self):
        return os.path.join(self.workspace.root, self.node)

    def find_targets(self, reference):
        if reference.wildcard:
            yield from self.targets.values()
        elif not reference.target_name:
            raise ValueError(
                "Reference {reference} does not contain a target".format(
                    reference=reference
                )
            )
        elif reference not in self.targets:
            raise KeyError(
                "Target {target} not found in package {package}".format(
                    target=reference.target_name,
                    package=reference.package_part
                )
            )
        else:
            yield self.targets[reference]
