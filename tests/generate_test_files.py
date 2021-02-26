"""Function to create base files used for tests."""
import copy
import json
import tempfile
from pathlib import Path

import rst2pdf.createpdf
import yaml

REF_DICT = {
    "int_value": 1,
    "simple_list": [1, 2.5, "str_val"],
    "nested_list": [
        1,
        2.5,
        "str_val",
        [
            "nested_list_val",
            {
                "nested_dict_key_1": "nested_dict_val_1",
                "nested_dict_key_2": "nested_dict_val_2",
                "nested_list_key": [1, 2.5, "str_val"],
            },
        ],
    ],
    "simple_dict": {
        "dict_key_1": [1, 2, 3],
        "dict_key_2": [1, 2, 3],
    },
    "nested_dict": {
        "dict_key": [1, 2, 3],
        "sub_nested_dict": {
            "nested_dict_key": "nested_dict_val",
            "nested_list_key": [1, 2.5, "str_val"],
        },
    },
    "nested_dict_test": 0,
}

DIFF_DICT = {
    "int_value": 2,
    "simple_list": [2, 2.50001, "#str_val#"],
    "nested_list": [
        2,
        2.50001,
        "#str_val#",
        [
            "#nested_list_val#",
            {
                "nested_dict_key_1": "#nested_dict_val_1#",
                "#nested_dict_key_2#": "nested_dict_val_2",
                "nested_list_key": [2, 2.50001, "#str_val#"],
            },
        ],
    ],
    "simple_dict": {
        "dict_key_1": [1, 4, 3],
        "#dict_key_2#": [1, 2, 3],
        "#dict_key_3#": [1, 2, 3],
        "#dict_key_4#": [1, 2, 3],
    },
    "simple_list_test": [
        ("dict_key_1", [1, 4, 3]),
        ("#dict_key_2#", [1, 2, 3]),
    ],
    "nested_dict": {
        "dict_key": [1, 4, 3],
        "sub_nested_dict": {
            "nested_dict_key_1": "#nested_dict_val_1#",
            "#nested_dict_key_2#": "nested_dict_val_2",
            "nested_list_key": [2, 2.50001, "#str_val#"],
        },
    },
}

REF_RST = r"""
This is a test file
===================

This is a random sentence.

This is a simple math formula:

.. math::

    x = 3 \times y^2

"""

DIFF_RST = r"""
This is a test file
===================

This is **a** random sentence.

This is a simple math formula:

.. math::

    x = 8 \times y^2

"""


def create_json(filename, diff=False):
    """Create a JSON file."""
    if diff:
        data = copy.deepcopy(DIFF_DICT)
    else:
        data = copy.deepcopy(REF_DICT)
    with open(filename, "w") as f:
        json.dump(data, f)


def create_yaml(filename, diff=False):
    """Create a YAML file."""
    if diff:
        data = copy.deepcopy(DIFF_DICT)
    else:
        data = copy.deepcopy(REF_DICT)
    with open(filename, "w") as f:
        yaml.dump(data, f)


def create_pdf(filename, diff=False):
    """Create a PDF file."""
    if diff:
        data = copy.deepcopy(DIFF_RST)
    else:
        data = copy.deepcopy(REF_RST)
    with tempfile.TemporaryDirectory() as tmp_dir:
        rst_file = Path(tmp_dir) / Path(filename.name).with_suffix(".rst")
        with open(rst_file, "w") as f:
            f.write(data)
        rst2pdf.createpdf.main([str(rst_file), "-o", str(filename)])