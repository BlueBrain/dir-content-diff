"""Function to create base files used for tests."""
import configparser
import copy
import json
import tempfile
from pathlib import Path

import rst2pdf.createpdf
import yaml
from dicttoxml import dicttoxml

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
    "simple_list": [2, 2.50001, "__str_val__"],
    "nested_list": [
        2,
        2.50001,
        "__str_val__",
        [
            "__nested_list_val__",
            {
                "nested_dict_key_1": "__nested_dict_val_1__",
                "__nested_dict_key_2__": "nested_dict_val_2",
                "nested_list_key": [2, 2.50001, "__str_val__"],
            },
        ],
    ],
    "simple_dict": {
        "dict_key_1": [1, 4, 3],
        "__dict_key_2__": [1, 2, 3],
        "__dict_key_3__": [1, 2, 3],
        "__dict_key_4__": [1, 2, 3],
    },
    "simple_list_test": [
        ("dict_key_1", [1, 4, 3]),
        ("__dict_key_2__", [1, 2, 3]),
    ],
    "nested_dict": {
        "dict_key": [1, 4, 3],
        "sub_nested_dict": {
            "nested_dict_key_1": "__nested_dict_val_1__",
            "__nested_dict_key_2__": "nested_dict_val_2",
            "nested_list_key": [2, 2.50001, "__str_val__"],
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
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f)


def create_yaml(filename, diff=False):
    """Create a YAML file."""
    if diff:
        data = copy.deepcopy(DIFF_DICT)
    else:
        data = copy.deepcopy(REF_DICT)
    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def create_xml(filename, diff=False):
    """Create a YAML file."""
    if diff:
        data = copy.deepcopy(DIFF_DICT)
    else:
        data = copy.deepcopy(REF_DICT)

    with open(filename, "w", encoding="utf-8") as f:
        xml_data = dicttoxml(data).decode("utf-8")
        # Remove a type attribute for test purpose
        xml_data = xml_data.replace('nested_dict_key_1 type="str"', "nested_dict_key_1")
        f.write(xml_data)


REF_INI = {
    "section1": {
        "attr1": "val1",
        "attr2": 1,
    },
    "section2": {"attr3": [1, 2, "a", "b"], "attr4": {"a": 1, "b": [1, 2]}},
}
DIFF_INI = {
    "section1": {
        "attr1": "val2",
        "attr2": 2,
    },
    "section2": {"attr3": [1, 3, "a", "c"], "attr4": {"a": 4, "b": [1, 3]}},
}


def create_ini(filename, diff=False):
    """Create a INI file."""
    ini_data = configparser.ConfigParser()
    if diff:
        data = copy.deepcopy(DIFF_INI)
    else:
        data = copy.deepcopy(REF_INI)
    data["section2"]["attr3"] = json.dumps(data["section2"]["attr3"])
    data["section2"]["attr4"] = json.dumps(data["section2"]["attr4"])
    ini_data.read_dict(data)
    with open(filename, "w", encoding="utf-8") as f:
        ini_data.write(f)


def create_pdf(filename, diff=False):
    """Create a PDF file."""
    if diff:
        data = copy.deepcopy(DIFF_RST)
    else:
        data = copy.deepcopy(REF_RST)
    with tempfile.TemporaryDirectory() as tmp_dir:
        rst_file = Path(tmp_dir) / Path(filename.name).with_suffix(".rst")
        with open(rst_file, "w", encoding="utf-8") as f:
            f.write(data)

        try:
            rst2pdf.createpdf.main([str(rst_file), "-o", str(filename)])
        except SystemExit as exc:
            if exc.code != 0:
                raise exc
