import os

SASHIMMI_ROOT_NODE = ".sashimmi"
SASHIMMI_BIN_NODE = "bin"
SASHIMMI_SHIMS_NODE = "shims.yaml"
SASHIMMI_PACKAGE_NODE = ".sashimmi.yaml"
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
