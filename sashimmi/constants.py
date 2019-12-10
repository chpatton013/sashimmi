import os

SASHIMMI_ROOT_NODE = ".sashimmi"
SASHIMMI_BIN_NODE = "bin"
SASHIMMI_SHIMS_NODE = "shims.yaml"
SASHIMMI_PACKAGE_NODE = ".sashimmi.yaml"

_DEFAULT_SASHIMMI_MULTI_ROOT_NODE = os.path.join(
    os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
    "sashimultimmi",
)
SASHIMMI_MULTI_ROOT_NODE = os.environ.get(
    "SASHIMMI_MULTI_ROOT", _DEFAULT_SASHIMMI_MULTI_ROOT_NODE
)
SASHIMMI_MULTI_BIN_NODE = "bin"
SASHIMMI_MULTI_SHIMS_NODE = "shims"

ROOT_ANCHOR_TOKEN = "//"
REFERENCE_PATH_SEPARATOR_TOKEN = "/"
REFERENCE_PART_SEPARATOR_TOKEN = ":"
TARGET_SUBSTITUTION_TOKEN = "%"
PACKAGE_WILDCARD_TOKEN = "all"
RECURSIVE_WILDCARD_TOKEN = "..."


def root_node(root):
    return os.path.join(root, SASHIMMI_ROOT_NODE)


def bin_node(root):
    return os.path.join(root, SASHIMMI_ROOT_NODE, SASHIMMI_BIN_NODE)


def shims_node(root):
    return os.path.join(root, SASHIMMI_ROOT_NODE, SASHIMMI_SHIMS_NODE)


def multi_root_node():
    return SASHIMMI_MULTI_ROOT_NODE


def multi_bin_node():
    return os.path.join(SASHIMMI_MULTI_ROOT_NODE, SASHIMMI_MULTI_BIN_NODE)


def multi_shims_node():
    return os.path.join(SASHIMMI_MULTI_ROOT_NODE, SASHIMMI_MULTI_SHIMS_NODE)


def multi_shim_node(name):
    return os.path.join(multi_shims_node(), name)
