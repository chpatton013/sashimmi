import re


def validate_target_name_charset(name, reference):
    if re.search("[^a-zA-Z0-9._-]", name):
        raise ValueError(
            "Target name '{name}' in reference {reference} contains illegal characters."
            .format(name=name, reference=reference)
        )
