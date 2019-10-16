import abc

from ..models.workspace import Workspace
from ._internal import find_root_directory, ensure_workspace

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
        root = find_root_directory(args.root)
        ensure_workspace(root)
        self.run(args, Workspace.make(root))

    @abc.abstractmethod
    def run(self, args, workspace):
        pass
