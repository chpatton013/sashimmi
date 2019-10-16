import os
import pathlib

from ..constants import root_node, bin_node, shims_node


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


def _ensure_bin_node(root):
    pathlib.Path(bin_node(root)).mkdir(exist_ok=True)


def _ensure_shims_node(root):
    pathlib.Path(shims_node(root)).touch()


def ensure_root_node(root):
    pathlib.Path(root_node(root)).mkdir(exist_ok=True)


def ensure_workspace(root):
    _ensure_bin_node(root)
    _ensure_shims_node(root)
