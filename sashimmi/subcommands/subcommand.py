import abc
import fcntl
import os
import stat

from ..constants import lock_node, multi_lock_node
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


class WorkspaceLockBase(metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.name = name
        self.fd = None

    def __enter__(self):
        self.fd = self.open(self.name)
        os.chmod(
            self.name,
            stat.S_ISGID | stat.S_ENFMT | stat.S_IRUSR | stat.S_IWUSR |
            stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
        )
        self.lock(self.fd)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        self.fd.close()
        self.fd = None

    @abc.abstractmethod
    def open(self, name):
        pass

    @abc.abstractmethod
    def lock(self, fd):
        pass


class WorkspaceReadLock(WorkspaceLockBase):
    def __init__(self, name):
        super().__init__(name)

    def open(self, name):
        return open(name, "r")

    def lock(self, fd):
        fcntl.flock(fd, fcntl.LOCK_SH)


class WorkspaceWriteLock(WorkspaceLockBase):
    def __init__(self, name):
        super().__init__(name)

    def open(self, name):
        return open(name, "w")

    def lock(self, fd):
        fcntl.flock(fd, fcntl.LOCK_EX)


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


class SubcommandBaseWithWorkspaceLock(
    SubcommandBaseWithWorkspace, metaclass=abc.ABCMeta
):
    def make_workspace_lock(self, root):
        return self.make_lock(lock_node(root))

    def make_multi_lock(self):
        return self.make_lock(multi_lock_node())

    def run(self, args, workspace):
        with self.make_workspace_lock(workspace.root) as lock:
            self.run_with_lock(args, workspace, lock)

    @abc.abstractmethod
    def make_lock(self, name):
        pass

    @abc.abstractmethod
    def run_with_lock(self, args, workspace, lock):
        pass


class SubcommandBaseWithWorkspaceReadLock(
    SubcommandBaseWithWorkspaceLock, metaclass=abc.ABCMeta
):
    def make_lock(self, name):
        return WorkspaceReadLock(name)


class SubcommandBaseWithWorkspaceWriteLock(
    SubcommandBaseWithWorkspaceLock, metaclass=abc.ABCMeta
):
    def make_lock(self, name):
        return WorkspaceWriteLock(name)
