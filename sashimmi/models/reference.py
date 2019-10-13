import enum
import os

from ..constants import (
    SASHIMMI_PACKAGE_NODE,
    ROOT_ANCHOR_TOKEN,
    REFERENCE_PATH_SEPARATOR_TOKEN,
    REFERENCE_PART_SEPARATOR_TOKEN,
    PACKAGE_WILDCARD_TOKEN,
    RECURSIVE_WILDCARD_TOKEN,
)
from .validation import validate_target_name_charset


def _validate_reference_target_name(name, argument):
    if name == RECURSIVE_WILDCARD_TOKEN:
        raise ValueError(
            "Target name '{name}' in reference {reference} is reserved".format(
                name=name, reference=argument
            )
        )
    validate_target_name_charset(name, argument)


def _canonicalize_package_path(argument, root, cwd):
    if argument.startswith(ROOT_ANCHOR_TOKEN):
        package_path = argument.partition(ROOT_ANCHOR_TOKEN)[2]
    else:
        root_to_cwd = os.path.relpath(cwd, start=root)
        package_path = os.path.normpath(os.path.join(root_to_cwd, argument))

    normalized = os.path.normpath(package_path)
    if normalized == ".." or normalized.startswith("../"):
        raise ValueError(
            "Reference argument {argument} reaches outside of workspace".format(
                argument=argument
            )
        )
    return "" if normalized == "." else normalized


class Reference:
    class Wildcard(enum.Enum):
        PACKAGE_WILDCARD = 1
        RECURSIVE_WILDCARD = 2

    @staticmethod
    def make(argument, root, cwd=os.getcwd()):
        package_part, _, target_name = argument.partition(
            REFERENCE_PART_SEPARATOR_TOKEN
        )

        _validate_reference_target_name(target_name, argument)

        package_wildcard = (target_name == PACKAGE_WILDCARD_TOKEN)
        recursive_wildcard = (
            package_part == RECURSIVE_WILDCARD_TOKEN or package_part.endswith(
                "{separator}{token}".format(
                    separator=REFERENCE_PATH_SEPARATOR_TOKEN,
                    token=RECURSIVE_WILDCARD_TOKEN
                )
            )
        )
        if recursive_wildcard and target_name:
            raise ValueError(
                "Reference argument {argument} contains a recursive wildcard and target name"
                .format(argument=argument)
            )

        non_wildcard_package_part = package_part.partition(
            RECURSIVE_WILDCARD_TOKEN
        )[0]
        package_path = _canonicalize_package_path(
            non_wildcard_package_part, root, cwd
        )

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
            return "{anchor}{package_path}{separator}{target_name}".format(
                anchor=ROOT_ANCHOR_TOKEN,
                package_path=self.package_path,
                separator=REFERENCE_PART_SEPARATOR_TOKEN,
                target_name=self.target_name
            )
        elif self.wildcard == Reference.Wildcard.PACKAGE_WILDCARD:
            return "{anchor}{package_path}{separator}{token}".format(
                anchor=ROOT_ANCHOR_TOKEN,
                package_path=self.package_path,
                separator=REFERENCE_PART_SEPARATOR_TOKEN,
                token=PACKAGE_WILDCARD_TOKEN
            )
        elif self.wildcard == Reference.Wildcard.RECURSIVE_WILDCARD:
            return "{anchor}{package_path}{separator}{token}".format(
                anchor=ROOT_ANCHOR_TOKEN,
                package_path=self.package_path,
                separator=REFERENCE_PATH_SEPARATOR_TOKEN,
                token=RECURSIVE_WILDCARD_TOKEN
            )
        else:
            return "{anchor}{package_path}".format(
                anchor=ROOT_ANCHOR_TOKEN, package_path=self.package_path
            )

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
        return other.package_path.startswith(
            "{path}{separator}".format(
                path=self.package_path,
                separator=REFERENCE_PATH_SEPARATOR_TOKEN
            )
        )

    def is_child_of(self, other):
        return other.is_parent_of(self)
