import re

from ..constants import TARGET_SUBSTITUTION_TOKEN


def _generate_replacements(substitutions, target):
    for search, replace in substitutions.items():
        pattern = r"(^|[^{sub}]){sub}{search}\b".format(
            sub=TARGET_SUBSTITUTION_TOKEN, search=search
        )
        repl = r"\1{replace}".format(replace=replace(target))
        yield pattern, repl
    pattern = r"(^|[^{sub}]){sub}{sub}".format(sub=TARGET_SUBSTITUTION_TOKEN)
    repl = r"\1{sub}".format(sub=TARGET_SUBSTITUTION_TOKEN)
    yield pattern, repl


def substitute_string(value, target, substitutions, apply_substitutions=True):
    if not apply_substitutions:
        return value

    value = value[:]
    for pattern, repl in _generate_replacements(substitutions, target):
        value = re.sub(pattern, repl, value)
    return value


def substitute_list(items, target, substitutions, apply_substitutions=True):
    if not apply_substitutions:
        return items

    return [
        substitute_string(
            value,
            target,
            substitutions,
            apply_substitutions=apply_substitutions,
        ) for value in items
    ]


def substitute_dict(mapping, target, substitutions, apply_substitutions=True):
    if not apply_substitutions:
        return mapping

    return {
        key: substitute_string(
            value,
            target,
            substitutions,
            apply_substitutions=apply_substitutions,
        )
        for key, value in mapping.items()
    }
