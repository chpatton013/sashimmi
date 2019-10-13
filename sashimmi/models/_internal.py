import yaml


def load_yaml_document(file_path):
    document = yaml.safe_load(open(file_path, "r"))
    return document if document else {}
