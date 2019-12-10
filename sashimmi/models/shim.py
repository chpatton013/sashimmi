import hashlib
import os
import pathlib
import shutil

from ..constants import (
    root_node,
    bin_node,
    shims_node,
    multi_bin_node,
    multi_shims_node,
    multi_shim_node,
)
from ._internal import load_yaml_document
from .reference import Reference

SHIM_TEMPLATE = """\
#!/usr/bin/env bash
set -euo pipefail
exec sashimmi --root={root} run {reference} "$@"
"""


class Shim:
    def __init__(self, name, reference):
        self.name = name
        self.reference = reference


def _delete_file_or_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.unlink(path)


def _delete_all_shim_files(bin_root):
    for entry in os.listdir(bin_root):
        _delete_file_or_dir(os.path.join(bin_root, entry))


def _delete_all_multishim_files(bin_root):
    multi_shims_root = multi_shims_node()
    for shim_name in os.listdir(multi_shims_root):
        for entry in os.listdir(os.path.join(multi_shims_root, shim_name)):
            entry_path = os.path.join(multi_shims_root, shim_name, entry)
            destination = os.readlink(entry_path)
            if destination.startswith(bin_root):
                _delete_file_or_dir(entry_path)

    multi_bin_root = multi_bin_node()
    for entry in os.listdir(multi_bin_root):
        entry_path = os.path.join(multi_bin_root, entry)
        destination = os.readlink(entry_path)
        if not os.path.exists(destination):
            _delete_file_or_dir(entry_path)


def _sha256(content):
    sha256 = hashlib.sha256()
    sha256.update(content.encode("utf-8"))
    return sha256.hexdigest()


def read_shims_node(root):
    document = load_yaml_document(shims_node(root))
    if document is None:
        return {}
    if not type(document) is dict:
        raise ValueError("Shims file is invalid")
    return {
        name: Shim(name, Reference.make(reference, root, root))
        for name, reference in document.items()
    }


def write_shims_node(root, shims):
    content = ""
    for shim in sorted(shims.values(), key=lambda shim: shim.reference):
        content += "{name}: {reference}\n".format(
            name=shim.name, reference=shim.reference
        )
    open(shims_node(root), "w").write(content)


def bind_shims(root, shims, bind_multi):
    bin_root = bin_node(root)

    if bind_multi:
        _delete_all_multishim_files(bin_root)
    _delete_all_shim_files(bin_root)

    for shim in shims.values():
        shim_file = os.path.join(bin_root, shim.name)
        with open(shim_file, "w") as handle:
            handle.write(
                SHIM_TEMPLATE.format(root=root, reference=shim.reference)
            )
        os.chmod(shim_file, 0o775)

        if bind_multi:
            multi_shim_root = multi_shim_node(shim.name)
            multi_shim_file = os.path.join(multi_shim_root, _sha256(root))
            multi_bin_file = os.path.join(multi_bin_node(), shim.name)

            pathlib.Path(multi_shim_root).mkdir(exist_ok=True)
            os.symlink(shim_file, multi_shim_file)
            os.symlink(multi_shim_file, multi_bin_file)
