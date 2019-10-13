import os
import shutil

from ..constants import root_node, bin_node, shims_node
from ._internal import load_yaml_document
from .reference import Reference

SHIM_TEMPLATE = """\
#!/usr/bin/env bash
set -euo pipefail
exec sashimmi run {reference}
"""


class Shim:
    def __init__(self, name, reference):
        self.name = name
        self.reference = reference


def _delete_all_shim_files(root):
    for entry in os.listdir(root):
        entry_path = os.path.join(root, entry)
        if os.path.isdir(entry_path):
            shutil.rmtree(entry_path)
        else:
            os.unlink(entry_path)


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


def bind_shims(root, shims):
    _delete_all_shim_files(bin_node(root))

    for shim in shims.values():
        shim_file = os.path.join(bin_node(root), shim.name)
        with open(shim_file, "w") as handle:
            handle.write(
                SHIM_TEMPLATE.format(name=shim.name, reference=shim.reference)
            )
        os.chmod(shim_file, 0o775)
