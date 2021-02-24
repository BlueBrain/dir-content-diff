"""Module containing the base comparators."""
import json

import dictdiffer
import yaml
from diff_pdf_visually import pdfdiff

from dir_content_diff.util import diff_msg_formatter

_ACTION_MAPPING = {
    "add": "Added the value(s) '{value}' in the '{key}' key.",
    "change": "Changed the value of '{key}' from {value[0]} to {value[1]}.",
    "remove": "Removed the value(s) '{value}' from '{key}' key.",
}

_MAX_COMPARE_LENGHT = 50


def _format_key(key):
    if isinstance(key, str):
        key = key.split(".")
    if key == [""]:
        key = []
    return "".join(f"[{k}]" for k in key)


def _format_add_value(value):
    return json.dumps(dict(sorted(value)))


def _format_remove_value(value):
    return json.dumps(dict(sorted(value)))


def _format_change_value(value):
    value = list(value)
    for num, i in enumerate(value):
        if isinstance(i, str):
            value[num] = f"'{i}'"
        else:
            value[num] = str(i)
    return value


def compare_dicts(ref, comp, *args, **kwargs):
    """Compare two dictionaries.

    This function call :func:`dictdiffer.diff` and format its output. The args and kwargs are
    directly passed to this function, see the detail in the doc of this function.

    Args:
        ref (dict): The reference dictionary.
        comp (dict): The compared dictionary.

    Returns:
        bool or str: True if the dictionaries are considered as equal or a string explaining why
        they are not considered as equal.
    """
    format_mapping = {
        "add": _format_add_value,
        "remove": _format_remove_value,
        "change": _format_change_value,
    }

    if len(args) > 5:
        dot_notation = args[5]
        args = args[:5] + args[6:]
    else:
        dot_notation = kwargs.pop("dot_notation", False)
    kwargs["dot_notation"] = dot_notation
    res = list(dictdiffer.diff(ref, comp, *args, **kwargs))

    if not res:
        return True

    res_formatted = sorted(
        _ACTION_MAPPING[action].format(key=_format_key(key), value=format_mapping[action](value))
        for action, key, value in res[:_MAX_COMPARE_LENGHT]
    )
    res_str = "\n".join(res_formatted)
    return res_str


def compare_json_files(ref_path, comp_path, *args, **kwargs):
    """Compare data from two JSON files.

    This function calls :func:`compare_dicts`, see in the doc of this function for details on args
    and kwargs.
    """
    with open(ref_path) as file:
        ref = json.load(file)
    with open(comp_path) as file:
        comp = json.load(file)
    res = compare_dicts(ref, comp, *args, **kwargs)
    return diff_msg_formatter(ref_path, comp_path, res, args, kwargs)


def compare_yaml_files(ref_path, comp_path, *args, **kwargs):
    """Compare data from two YAML files.

    This function calls :func:`compare_dicts`, see in the doc of this function for details on args
    and kwargs.
    """
    with open(ref_path) as file:
        ref = yaml.load(file)
    with open(comp_path) as file:
        comp = yaml.load(file)
    res = compare_dicts(ref, comp, *args, **kwargs)
    return diff_msg_formatter(ref_path, comp_path, res, args, kwargs)


def compare_pdf_files(ref_path, comp_path, *args, **kwargs):
    """Compare two PDF files.

    This function calls :func:`diff_pdf_visually.pdfdiff`, see in the doc of this function for
    details on args and kwargs here:
    https://github.com/bgeron/diff-pdf-visually/blob/main/diff_pdf_visually/diff.py
    """
    res = pdfdiff(ref_path, comp_path, *args, **kwargs)
    return diff_msg_formatter(ref_path, comp_path, res, args, kwargs)
