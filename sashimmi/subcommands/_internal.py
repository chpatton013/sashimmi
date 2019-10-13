import abc
import os
import pathlib

from ..constants import root_node, bin_node, shims_node
from ..models.workspace import Workspace

SUBCOMMAND_REGISTRY = {}


def register_subcommand(subcommand):
    name = subcommand.name()
    if name in SUBCOMMAND_REGISTRY:
        raise ValueError(
            "Subcommand with name '{name}' already registered".format(
                name=name
            )
        )
    SUBCOMMAND_REGISTRY[name] = subcommand


def get_subcommand(name):
    return SUBCOMMAND_REGISTRY[name]


def get_subcommands():
    yield from SUBCOMMAND_REGISTRY.values()


def find_root_directory(root, original_root=None):
    if original_root is None:
        original_root = root

    if root == "/":
        raise RuntimeError(
            "Failed to locate sashimmi root from '{directory}'".format(
                directory=original_root
            )
        )

    if os.path.isdir(root_node(root)):
        return root
    else:
        return find_root_directory(os.path.dirname(root), original_root)


def ensure_root_node(root):
    pathlib.Path(root_node(root)).mkdir(exist_ok=True)


def ensure_bin_node(root):
    pathlib.Path(bin_node(root)).mkdir(exist_ok=True)


def ensure_shims_node(root):
    pathlib.Path(shims_node(root)).touch()


class SubcommandBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def name():
        pass

    @abc.abstractmethod
    def help():
        pass

    @abc.abstractmethod
    def configure_subparser(subparser):
        pass

    @abc.abstractmethod
    def main(self, args):
        pass


class SubcommandBaseWithWorkspace(SubcommandBase, metaclass=abc.ABCMeta):
    def main(self, args):
        self.run(args, Workspace.make(find_root_directory(args.root)))

    @abc.abstractmethod
    def run(self, args, workspace):
        pass
