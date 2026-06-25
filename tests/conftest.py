"""Configuration for the pytest test suite."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2026 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

# pylint: disable=redefined-outer-name
from pathlib import Path

import pandas as pd
import pytest

import dir_content_diff

from . import generate_test_files

pytest_plugins = ["pytester"]


@pytest.fixture
def registry_reseter():
    """Fixture to automatically reset the registry before and after a test."""
    dir_content_diff.reset_comparators()
    yield None
    dir_content_diff.reset_comparators()


@pytest.fixture
def empty_ref_tree(tmpdir):
    """Empty reference directory."""
    tree = Path(tmpdir) / "ref"
    tree.mkdir()
    return tree


@pytest.fixture
def empty_res_tree(tmpdir):
    """Empty result directory."""
    tree = Path(tmpdir) / "res"
    tree.mkdir()
    return tree


@pytest.fixture
def ref_tree(empty_ref_tree):
    """Reference directory tree."""
    generate_test_files.create_pdf(empty_ref_tree / "file.pdf")
    generate_test_files.create_json(empty_ref_tree / "file.json")
    generate_test_files.create_yaml(empty_ref_tree / "file.yaml")
    generate_test_files.create_xml(empty_ref_tree / "file.xml")
    generate_test_files.create_ini(empty_ref_tree / "file.ini")
    return empty_ref_tree


@pytest.fixture
def res_tree_equal(empty_res_tree):
    """Result directory tree equal to the reference."""
    generate_test_files.create_pdf(empty_res_tree / "file.pdf")
    generate_test_files.create_json(empty_res_tree / "file.json")
    generate_test_files.create_yaml(empty_res_tree / "file.yaml")
    generate_test_files.create_xml(empty_res_tree / "file.xml")
    generate_test_files.create_ini(empty_res_tree / "file.ini")
    return empty_res_tree


@pytest.fixture
def res_tree_diff(empty_res_tree):
    """Result directory tree different from the reference."""
    generate_test_files.create_pdf(empty_res_tree / "file.pdf", diff=True)
    generate_test_files.create_json(empty_res_tree / "file.json", diff=True)
    generate_test_files.create_yaml(empty_res_tree / "file.yaml", diff=True)
    generate_test_files.create_xml(empty_res_tree / "file.xml", diff=True)
    generate_test_files.create_ini(empty_res_tree / "file.ini", diff=True)
    return empty_res_tree


@pytest.fixture
def pdf_diff():
    """The diff that should be reported for the PDF files."""
    return (
        r"The files '\S*/file.pdf' and '\S*/file.pdf' are different\:\n"
        r"(Kwargs used for computing differences: {'verbosity': 0}\n)?"
        "The following pages are the most different: 1"
    )


@pytest.fixture
def dict_diff():
    """The diff that should be reported for the JSON and YAML files."""
    diff = (
        r"""The files '\S*' and '\S*' are different:\n"""
        r"""Added value at \['nested_dict'\]\['sub_nested_dict'\]\['__nested_dict_key_2__'\]: "nested_dict_val_2"\.\n"""
        r"""Added value at \['nested_dict'\]\['sub_nested_dict'\]\['nested_dict_key_1'\]: "__nested_dict_val_1__"\.\n"""
        r"""Added value at \['nested_list'\]\[3\]\[1\]\['__nested_dict_key_2__'\]: "nested_dict_val_2"\.\n"""
        r"""Added value at \['simple_dict'\]\['__dict_key_2__'\]: \[1, 2, 3\]\.\n"""
        r"""Added value at \['simple_dict'\]\['__dict_key_3__'\]: \[1, 2, 3\]\.\n"""
        r"""Added value at \['simple_dict'\]\['__dict_key_4__'\]: \[1, 2, 3\]\.\n"""
        r"""Added value at \['simple_list_test'\]: \[\["dict_key_1", \[1, 4, 3\]\], """
        r"""\["__dict_key_2__", \[1, 2, 3\]\]\]\.\n"""
        r"""Changed value at \['int_value'\]: 1 -> 2\.\n"""
        r"""Changed value at \['nested_dict'\]\['dict_key'\]\[1\]: 2 -> 4\.\n"""
        r"""Changed value at \['nested_dict'\]\['sub_nested_dict'\]\['nested_list_key'\]\[0\]: 1 -> 2\.\n"""
        r"""Changed value at \['nested_dict'\]\['sub_nested_dict'\]\['nested_list_key'\]\[1\]: 2.5 -> 2.50001\.\n"""
        r"""Changed value at \['nested_dict'\]\['sub_nested_dict'\]\['nested_list_key'\]"""
        r"""\[2\]: "str_val" -> "__str_val__"\.\n"""
        r"""Changed value at \['nested_list'\]\[0\]: 1 -> 2\.\n"""
        r"""Changed value at \['nested_list'\]\[1\]: 2.5 -> 2.50001\.\n"""
        r"""Changed value at \['nested_list'\]\[2\]: "str_val" -> "__str_val__"\.\n"""
        r"""Changed value at \['nested_list'\]\[3\]\[0\]: "nested_list_val" -> "__nested_list_val__"\.\n"""
        r"""Changed value at \['nested_list'\]\[3\]\[1\]\['nested_dict_key_1'\]: """
        r""""nested_dict_val_1" -> "__nested_dict_val_1__"\.\n"""
        r"""Changed value at \['nested_list'\]\[3\]\[1\]\['nested_list_key'\]\[0\]: 1 -> 2\.\n"""
        r"""Changed value at \['nested_list'\]\[3\]\[1\]\['nested_list_key'\]\[1\]: 2.5 -> 2.50001\.\n"""
        r"""Changed value at \['nested_list'\]\[3\]\[1\]\['nested_list_key'\]\[2\]: "str_val" -> "__str_val__"\.\n"""
        r"""Changed value at \['simple_dict'\]\['dict_key_1'\]\[1\]: 2 -> 4\.\n"""
        r"""Changed value at \['simple_list'\]\[0\]: 1 -> 2\.\n"""
        r"""Changed value at \['simple_list'\]\[1\]: 2.5 -> 2.50001\.\n"""
        r"""Changed value at \['simple_list'\]\[2\]: "str_val" -> "__str_val__"\.\n"""
        r"""Removed value at \['nested_dict'\]\['sub_nested_dict'\]\['nested_dict_key'\]: "nested_dict_val"\.\n"""
        r"""Removed value at \['nested_dict_test'\]: 0\.\n"""
        r"""Removed value at \['nested_list'\]\[3\]\[1\]\['nested_dict_key_2'\]: "nested_dict_val_2"\.\n"""
        r"""Removed value at \['simple_dict'\]\['dict_key_2'\]: \[1, 2, 3\]\."""
    )
    return diff


@pytest.fixture
def base_diff():
    """The diff that should be reported for the XML files."""
    return r"The files '\S*/file\..{3,4}' and '\S*/file\..{3,4}' are different\."


@pytest.fixture
def xml_diff(dict_diff):
    """The diff that should be reported for the XML files."""
    return dict_diff.replace(r"value at \[", r"value at \['root'\]\[")


@pytest.fixture
def ini_diff():
    """The diff that should be reported for the INI files."""
    diff = (
        r"The files '\S*/file\.ini' and '\S*/file\.ini' are different:\n"
        r"""Changed value at \['section1'\]\['attr1'\]: "val1" -> "val2"\.\n"""
        r"""Changed value at \['section1'\]\['attr2'\]: 1 -> 2\.\n"""
        r"""Changed value at \['section2'\]\['attr3'\]\[1\]: 2 -> 3\.\n"""
        r"""Changed value at \['section2'\]\['attr3'\]\[3\]: "b" -> "c"\.\n"""
        r"""Changed value at \['section2'\]\['attr4'\]\['a'\]: 1 -> 4\.\n"""
        r"""Changed value at \['section2'\]\['attr4'\]\['b'\]\[1\]: 2 -> 3\."""
    )
    return diff


@pytest.fixture
def ref_csv(ref_tree):
    """The reference CSV file."""
    ref_data = {
        "col_a": [1, 2, 3],
        "col_b": ["a", "b", "c"],
        "col_c": [4, 5, 6],
    }
    df = pd.DataFrame(ref_data, index=["idx1", "idx2", "idx3"])
    filename = ref_tree / "file.csv"
    df.to_csv(filename, index=True, index_label="index")
    return filename


@pytest.fixture
def res_csv_equal(ref_csv, res_tree_equal):
    """The result CSV file equal to the reference."""
    df = pd.read_csv(ref_csv, index_col="index")
    filename = res_tree_equal / "file.csv"
    df.to_csv(filename, index=True, index_label="index")
    return filename


@pytest.fixture
def res_csv_diff(ref_csv, res_tree_diff):
    """The result CSV file different from the reference."""
    df = pd.read_csv(ref_csv, index_col="index")
    df.loc["idx1", "col_a"] *= 10
    df.loc["idx2", "col_b"] += "_new"
    filename = res_tree_diff / "file.csv"
    df.to_csv(filename, index=True, index_label="index")
    return filename


@pytest.fixture
def csv_diff():
    """The diff that should be reported for the CSV files."""
    return (
        r"""The files '\S*/file.csv' and '\S*/file.csv' are different:\n\n"""
        r"""Column 'col_a': Series are different\n\n"""
        r"""Series values are different \(33.33333 %\)\n"""
        r"""\[index\]: \[0, 1, 2\]\n"""
        r"""\[left\]:  \[1, 2, 3\]\n"""
        r"""\[right\]: \[10, 2, 3\]\n"""
        r"""(At positional index 0, first diff: 1 != 10\n)?\n"""
        r"""Column 'col_b': Series are different\n\n"""
        r"""Series values are different \(33.33333 %\)\n"""
        r"""\[index\]: \[0, 1, 2\]\n\[left\]:  \[a, b, c\]\n\[right\]: \[a, b_new, c\]"""
        r"""(\nAt positional index 1, first diff: b != b_new)?"""
    )
