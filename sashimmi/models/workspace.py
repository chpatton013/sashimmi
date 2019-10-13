import os

from ..constants import SASHIMMI_PACKAGE_NODE

from .package import Package
from .reference import Reference


def _find_packages(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for f in filenames:
            if f == SASHIMMI_PACKAGE_NODE:
                relative = os.path.relpath(dirpath, start=root)
                yield Reference.make(relative, root, root)


class Workspace:
    @staticmethod
    def make(root):
        packages = {
            reference: Package.make(root, reference)
            for reference in _find_packages(root)
        }
        return Workspace(root, packages)

    def __init__(self, root, packages):
        self.root = root
        self.packages = packages
        for package in self.packages.values():
            package.workspace = self

    def __str__(self):
        return "Workspace({root})".format(root=self.root)

    @property
    def node(self):
        return constants.root_node(self.root)

    def __find_package(self, reference):
        package_reference = reference.package_part
        if package_reference not in self.packages:
            if reference.wildcard == Reference.Wildcard.RECURSIVE_WILDCARD:
                return
            else:
                raise KeyError(
                    "Package {package} not found in workspace".format(
                        package=package_reference
                    )
                )
        yield self.packages[package_reference]

    def find_packages(self, reference):
        yield from self.__find_package(reference)
        if reference.wildcard == Reference.Wildcard.RECURSIVE_WILDCARD:
            for child_package in self.packages.values():
                if child_package.reference.is_child_of(reference):
                    yield child_package

    def find_targets(self, reference):
        for package in self.find_packages(reference):
            yield from package.find_targets(reference)
