import os
import pathlib

from ..constants import (
    root_node,
    bin_node,
    shims_node,
    multi_root_node,
    multi_bin_node,
    multi_shims_node,
)


def _ensure_file(path):
    pathlib.Path(path).touch()


def _ensure_directory(path):
    pathlib.Path(path).mkdir(exist_ok=True)


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
    _ensure_directory(root_node(root))


def ensure_bin_node(root):
    _ensure_directory(bin_node(root))


def ensure_shims_node(root):
    _ensure_file(shims_node(root))


def ensure_multi_root_node():
    _ensure_directory(multi_root_node())


def ensure_multi_bin_node():
    _ensure_directory(multi_bin_node())


def ensure_multi_shims_node():
    _ensure_directory(multi_shims_node())


def ensure_workspace(root):
    ensure_bin_node(root)
    ensure_shims_node(root)
    ensure_multi_root_node()
    ensure_multi_bin_node()
    ensure_multi_shims_node()
