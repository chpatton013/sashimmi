#!/usr/bin/env python3

import abc
import argparse
import enum
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys

import yaml


SASHIMMI_ROOT_NODE = ".sashimmi"
SASHIMMI_BIN_NODE = "bin"
SASHIMMI_SHIMS_NODE = "shims.yaml"
SASHIMMI_PACKAGE_NODE = ".sashimmi.yaml"
ROOT_ANCHOR_TOKEN = "//"
REFERENCE_PATH_SEPARATOR_TOKEN = "/"
REFERENCE_PART_SEPARATOR_TOKEN = ":"
PACKAGE_WILDCARD_TOKEN = "all"
RECURSIVE_WILDCARD_TOKEN = "..."
SHIM_TEMPLATE = """\
#!/usr/bin/env bash
set -euo pipefail
exec sashimmi run {reference}
"""


def _root_node(root):
    return os.path.join(root, SASHIMMI_ROOT_NODE)


def _bin_node(root):
    return os.path.join(root, SASHIMMI_ROOT_NODE, SASHIMMI_BIN_NODE)


def _shims_node(root):
    return os.path.join(root, SASHIMMI_ROOT_NODE, SASHIMMI_SHIMS_NODE)


def _find_root_directory(root):
    if root == "/":
        raise RuntimeError("Failed to locate sashimmi root from '{directory}'".format(directory=root))

    if os.path.isdir(_root_node(root)):
        return root
    else:
        return _find_root_directory(os.path.dirname(root))


def _validate_target_name_charset(name, reference):
    if re.search("[^a-zA-Z0-9._-]", name):
        raise ValueError("Target name '{name}' in reference {reference} contains illegal characters.".format(name=name, reference=reference))


class Reference:
    class Wildcard(enum.Enum):
        PACKAGE_WILDCARD = 1
        RECURSIVE_WILDCARD = 2

    @staticmethod
    def __validate_target_name(name, argument):
        if name == RECURSIVE_WILDCARD_TOKEN:
            raise ValueError("Target name '{name}' in reference {reference} is reserved".format(name=name, reference=argument))
        _validate_target_name_charset(name, argument)

    @staticmethod
    def __canonicalize_package_path(argument, root, cwd):
        if argument.startswith(ROOT_ANCHOR_TOKEN):
            package_path = argument.partition(ROOT_ANCHOR_TOKEN)[2]
        else:
            root_to_cwd = os.path.relpath(cwd, start=root)
            package_path = os.path.normpath(os.path.join(root_to_cwd, argument))

        normalized = os.path.normpath(package_path)
        if normalized == ".." or normalized.startswith("../"):
            raise ValueError("Reference argument {argument} reaches outside of workspace".format(argument=argument))
        return "" if normalized == "." else normalized

    @staticmethod
    def make(argument, root, cwd):
        package_part, _, target_name = argument.partition(REFERENCE_PART_SEPARATOR_TOKEN)

        Reference.__validate_target_name(target_name, argument)

        package_wildcard = (target_name == PACKAGE_WILDCARD_TOKEN)
        recursive_wildcard = (package_part == RECURSIVE_WILDCARD_TOKEN or package_part.endswith("{separator}{token}".format(separator=REFERENCE_PATH_SEPARATOR_TOKEN, token=RECURSIVE_WILDCARD_TOKEN)))
        if recursive_wildcard and target_name:
            raise ValueError("Reference argument {argument} contains a recursive wildcard and target name".format(argument=argument))

        non_wildcard_package_part = package_part.partition(RECURSIVE_WILDCARD_TOKEN)[0]
        package_path = Reference.__canonicalize_package_path(non_wildcard_package_part, root, cwd)

        assert not package_wildcard or not recursive_wildcard
        if package_wildcard:
            wildcard = Reference.Wildcard.PACKAGE_WILDCARD
        elif recursive_wildcard:
            wildcard = Reference.Wildcard.RECURSIVE_WILDCARD
        else:
            wildcard = None

        return Reference(package_path, target_name, wildcard=wildcard)

    def __init__(self, package_path, target_name, wildcard=None):
        self.package_path = package_path
        self.target_name = target_name
        self.wildcard = wildcard

    def __str__(self):
        if self.target_name:
            return "{anchor}{package_path}{separator}{target_name}".format(anchor=ROOT_ANCHOR_TOKEN, package_path=self.package_path, separator=REFERENCE_PART_SEPARATOR_TOKEN, target_name=self.target_name)
        elif self.wildcard == Reference.Wildcard.PACKAGE_WILDCARD:
            return "{anchor}{package_path}{separator}{token}".format(anchor=ROOT_ANCHOR_TOKEN, package_path=self.package_path, separator=REFERENCE_PART_SEPARATOR_TOKEN, token=PACKAGE_WILDCARD_TOKEN)
        elif self.wildcard == Reference.Wildcard.RECURSIVE_WILDCARD:
            return "{anchor}{package_path}{separator}{token}".format(anchor=ROOT_ANCHOR_TOKEN, package_path=self.package_path, separator=REFERENCE_PATH_SEPARATOR_TOKEN, token=RECURSIVE_WILDCARD_TOKEN)
        else:
            return "{anchor}{package_path}".format(anchor=ROOT_ANCHOR_TOKEN, package_path=self.package_path)

    def __eq__(self, other):
        return self.path == other.path

    def __lt__(self, other):
        if self.package_path < other.package_path:
            return True
        if self.target_name < other.target_name:
            return True
        return self.path < other.path

    def __hash__(self):
        return hash(self.path)

    @property
    def package_part(self):
        return Reference(self.package_path, None)

    @property
    def path(self):
        if self.target_name:
            return os.path.join(self.package_path, self.target_name)
        else:
            return self.package_path

    @property
    def package_node_path(self):
        return os.path.join(self.package_path, SASHIMMI_PACKAGE_NODE)

    def is_parent_of(self, other):
        if self.package_path == "" and other.package_path != "":
            return True
        return other.package_path.startswith("{path}{separator}".format(path=self.package_path, separator=REFERENCE_PATH_SEPARATOR_TOKEN))

    def is_child_of(self, other):
        return other.is_parent_of(self)


class Workspace:
    @staticmethod
    def __find_packages(root):
        for dirpath, _dirnames, filenames in os.walk(root):
            for f in filenames:
                if f == SASHIMMI_PACKAGE_NODE:
                    relative = os.path.relpath(dirpath, start=root)
                    yield Reference.make(relative, root, root)

    @staticmethod
    def make(root):
        packages = {
            reference: Package.make(root, reference)
            for reference in Workspace.__find_packages(root)
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
        return _root_node(self.root)

    def __find_package(self, reference):
        package_reference = reference.package_part
        if package_reference not in self.packages:
            raise KeyError("Package {package} not found in workspace".format(package=package_reference))
        return self.packages[package_reference]

    def find_packages(self, reference):
        yield self.__find_package(reference)
        if reference.wildcard == Reference.Wildcard.RECURSIVE_WILDCARD:
            for child_package in self.packages.values():
                if child_package.reference.is_child_of(reference):
                    yield child_package

    def find_targets(self, reference):
        for package in self.find_packages(reference):
            yield from package.find_targets(reference)


class Package:
    @staticmethod
    def __validate_name(name, reference):
        if name in (PACKAGE_WILDCARD_TOKEN, RECURSIVE_WILDCARD_TOKEN):
            raise ValueError("Target name '{name}' in package {package} is reserved".format(name=name, package=reference))
        _validate_target_name_charset(name, reference)

    @staticmethod
    def __load_targets(root, reference):
        document = yaml.safe_load(open(os.path.join(root, reference.package_node_path), "r"))
        names = set()
        for target in document.get("targets", []):
            if "name" not in target:
                raise KeyError("Target in package {package} is missing required attriute 'name'".format(package=reference))
            name = target["name"]

            Package.__validate_name(name, reference)

            if name in names:
                raise ValueError("Target name '{name}' is duplicated in packge {package}".format(name=name, package=reference))
            names.add(name)

            yield Reference(reference.package_path, name), target

    @staticmethod
    def make(root, package_reference):
        targets = {
            target_reference: Target.make(package_reference, target_yml)
            for target_reference, target_yml in Package.__load_targets(root, package_reference)
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
            raise ValueError("Reference {reference} does not contain a target".format(reference=reference))
        elif reference not in self.targets:
            raise KeyError("Target {target} not found in package {package}".format(target=reference.target_name, package=reference.package_part))
        else:
            yield self.targets[reference]


class Target:
    @staticmethod
    def make(package_reference, yml_node):
        if "name" not in yml_node:
            raise KeyError("Target in package {package} is missing required attriute 'name'".format(package_reference))
        target_reference = Reference(package_reference.package_path, yml_node["name"])

        components = []

        if DockerComponent.yaml_key() in yml_node:
            components.append(DockerComponent.make_from_yaml_node(yml_node[DockerComponent.yaml_key()], target_reference))

        if CommandComponent.yaml_key() in yml_node:
            components.append(CommandComponent.make_from_yaml_node(yml_node[CommandComponent.yaml_key()], target_reference))

        if len(components) == 0:
            raise KeyError("Target {target} is missing components".format(target_reference))

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
            raise KeyError("Command component in target {target} is missing required attriute 'executable'".format(target_reference))
        return CommandComponent(yaml_node["executable"], arguments=yaml_node.get("arguments"), variables=yaml_node.get("variables"))

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
            raise KeyError("Docker component in target {target} is missing required attriute 'image'".format(target_reference))
        return DockerComponent(yaml_node["image"], arguments=yaml_node.get("arguments"), variables=yaml_node.get("variables"))

    def __init__(self, image, arguments=None, variables=None):
        self.image = image
        self.arguments = arguments if arguments else []
        self.variables = variables if variables else {}

    def command_line_arguments(self):
        command = ["docker", "run"]
        command += ["--env={key}={value}".format(key=key, value=value) for key, value in self.variables.items()]
        command += self.arguments
        command.append(self.image)
        return command

    def environment_variables(self):
        return self.variables


class Shim:
    def __init__(self, name, reference):
        self.name = name
        self.reference = reference


def _ensure_root_node(root):
    pathlib.Path(_root_node(root)).mkdir(exist_ok=True)


def _ensure_bin_node(root):
    pathlib.Path(_bin_node(root)).mkdir(exist_ok=True)


def _ensure_shims_node(root):
    pathlib.Path(_shims_node(root)).touch()


def _read_shims_node(root):
    document = yaml.safe_load(open(_shims_node(root), "r"))
    if document is None:
        return {}
    if not type(document) is dict:
        raise ValueError("Shims file is invalid")
    return {
        name: Shim(name, Reference.make(reference, root, root))
        for name, reference in document.items()
    }


def _write_shims_node(root, shims):
    print(shims)
    content = ""
    for shim in sorted(shims.values(), key=lambda shim: shim.reference):
        content += "{name}: {reference}\n".format(name=shim.name, reference=shim.reference)
    open(_shims_node(root), "w").write(content)


def _bind_shims(root, shims):
    dirpath = _bin_node(root)
    for entry in os.listdir(dirpath):
        entry_path = os.path.join(dirpath, entry)
        if os.path.isdir(entry_path):
            shutil.rmtree(entry_path)
        else:
            os.unlink(entry_path)

    for shim in shims.values():
        shim_file = os.path.join(_bin_node(root), shim.name)
        with open(shim_file, "w") as handle:
            handle.write(SHIM_TEMPLATE.format(name=shim.name, reference=shim.reference))
        os.chmod(shim_file, 0o775)


def do_init(root, force=False):
    if not force:
        try:
            workspace = _find_root_directory(root)
        except RuntimeError:
            pass
        else:
            raise RuntimeError("Cannot initialize sashimmi workspace in '{root}' because a workspace already exists in '{workspace}'".format(root=root, workspace=workspace))

    _ensure_root_node(root)
    _ensure_bin_node(root)
    _ensure_shims_node(root)
    _write_shims_node(root, {})
    _bind_shims(root, {})
    print("Initialized new sashimmi workspace in '{root}'".format(root=root))


def do_shims(workspace):
    _ensure_bin_node(workspace.root)
    _ensure_shims_node(workspace.root)

    shims = _read_shims_node(workspace.root)
    print("Shims")
    for shim, target in shims.items():
        print("  {shim}: {target}".format(shim=shim, target=target))


def do_install(workspace, target_references, force=False):
    _ensure_bin_node(workspace.root)
    _ensure_shims_node(workspace.root)

    shims = _read_shims_node(workspace.root)
    for reference in target_references:
        for target in workspace.find_targets(reference):
            name = target.reference.target_name
            if name in shims:
                if force:
                    print("Overwriting shim '{name}' with target '{target}'".format(name=name, target=target.reference), file=sys.stderr)
                else:
                    raise ValueError("Shim '{name}' is already installed".format(name=name))
            shims[name] = Shim(name, target.reference)

    _write_shims_node(workspace.root, shims)
    _bind_shims(workspace.root, shims)


def do_uninstall(workspace, target_references):
    _ensure_bin_node(workspace.root)
    _ensure_shims_node(workspace.root)

    shims = _read_shims_node(workspace.root)
    for reference in target_references:
        for target in workspace.find_targets(reference):
            del shims[target.reference.target_name]

    _write_shims_node(workspace.root, shims)
    _bind_shims(workspace.root, shims)


def do_clean(workspace):
    _ensure_bin_node(workspace.root)
    _write_shims_node(workspace.root, {})
    _bind_shims(workspace.root, {})


def do_bind(workspace):
    _ensure_bin_node(workspace.root)
    shims = _read_shims_node(workspace.root)
    _bind_shims(workspace.root, shims)


def do_workspace(workspace):
    logging.debug("do_workspace(workspace=%s)", workspace)

    print("Packages")
    for package_reference in workspace.packages.keys():
        print("  {reference}".format(reference=package_reference))


def do_package(workspace, reference):
    logging.debug("do_package(workspace=%s, reference=%s)", workspace, reference)

    if reference.target_name:
        raise ValueError("Reference {reference} contains a target name".format(reference=reference))

    for package in workspace.find_packages(reference):
        print("{reference}".format(reference=package.reference))
        for target_reference in package.targets.keys():
            print("  :{target}".format(target=target_reference.target_name))


def do_target(workspace, references):
    logging.debug("do_target(workspace=%s, references=%s)", workspace, references)

    for reference in references:
        for target in workspace.find_targets(reference):
            environment_variables = [
                "{key}={value}".format(key=key, value=value)
                for key, value in target.environment_variables().items()
            ]
            print("{reference}\n  ENVIRONMENT: {environment}\n  COMMANDLINE: {command}".format(
                reference=target.reference,
                environment=" ".join(environment_variables),
                command=" ".join(target.command_line_arguments()),
            ))


def do_run(workspace, reference, arguments):
    logging.debug("do_run(workspace=%s, reference=%s, arguments=%s)", workspace, reference, arguments)

    if not reference.target_name:
        raise ValueError("Reference argument {argument} does not contain a target name".format(argument=reference))

    targets = [target for target in workspace.find_targets(reference)]
    if len(targets) > 1:
        raise ValueError("Reference argument {argument} produces multiple targets".format(argument=reference))
    target = targets[0]

    environment = os.environ.copy()
    environment.update(target.environment_variables())

    subprocess.check_call(target.command_line_arguments() + arguments, env=environment)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", default=False, help="Enable debug logging.")
    parser.add_argument("--root", default=os.getcwd(), help="Search for sashimmi root node from this alternate location instead of current working directory.")

    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = True

    parser_init = subparsers.add_parser("init", help="Initialize a new sashimmi workspace.")
    parser_init.add_argument("--force", action="store_true", default=False, help="Skip check for existing workspaces.")

    parser_shims = subparsers.add_parser("shims", help="Print the shims installed in this workspace.")

    parser_install = subparsers.add_parser("install", help="Install shims for these targets.")
    parser_install.add_argument("references", nargs="+", help="References of the targets which map to commands. Targets listed later take precedence.")
    parser_install.add_argument("--force", action="store_true", default=False, help="Allow targets with conflicting names override previously-installed shims.")

    parser_uninstall = subparsers.add_parser("uninstall", help="Uninstall shims for these targets.")
    parser_uninstall.add_argument("references", nargs="+", help="References of the targets which map to commands.")

    parser_clean = subparsers.add_parser("clean", help="Uninstall all shims.")

    parser_bind = subparsers.add_parser("bind", help="Bind all shims.")

    parser_workspace = subparsers.add_parser("workspace", help="Print the packages found in this workspace.")

    parser_package = subparsers.add_parser("package", help="Print the targets defined in these packages.")
    parser_package.add_argument("reference", help="References of the packages within the workspace.")

    parser_target = subparsers.add_parser("target", help="Print the commands these targets map to in this repository.")
    parser_target.add_argument("references", nargs="+", help="References of the targets which map to commands.")

    parser_run = subparsers.add_parser("run", help="Run the command this target maps to in this repository.")
    parser_run.add_argument("reference", help="Reference of the target which maps to a command.")
    parser_run.add_argument("arguments", nargs="*", help="Arguments to pass to command")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.subcommand == "init":
        do_init(args.root, force=args.force)
        return

    root = _find_root_directory(args.root)
    workspace = Workspace.make(root)

    if args.subcommand == "shims":
        do_shims(workspace)
    elif args.subcommand == "install":
        target_references = [
            Reference.make(reference, root, os.getcwd())
            for reference in args.references
        ]
        do_install(workspace, target_references, force=args.force)
    elif args.subcommand == "uninstall":
        target_references = [
            Reference.make(reference, root, os.getcwd())
            for reference in args.references
        ]
        do_uninstall(workspace, target_references)
    elif args.subcommand == "clean":
        do_clean(workspace)
    elif args.subcommand == "bind":
        do_bind(workspace)
    elif args.subcommand == "workspace":
        do_workspace(workspace)
    elif args.subcommand == "package":
        package_reference = Reference.make(args.reference, root, os.getcwd())
        do_package(workspace, package_reference)
    elif args.subcommand == "target":
        target_references = [
            Reference.make(reference, root, os.getcwd())
            for reference in args.references
        ]
        do_target(workspace, target_references)
    elif args.subcommand == "run":
        target_reference = Reference.make(args.reference, root, os.getcwd())
        do_run(workspace, target_reference, args.arguments)
    else:
        raise ValueError("Unknown subcommand '{subcommand}'".format(subcommand=args.subcommand))


if __name__ == "__main__":
    main()
