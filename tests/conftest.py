"""Prepare the tests."""
# pylint: disable=redefined-outer-name
from pathlib import Path

import pytest

import dir_content_diff

from . import generate_test_files


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
    return empty_ref_tree


@pytest.fixture
def res_tree_equal(empty_res_tree):
    """Result directory tree equal to the reference."""
    generate_test_files.create_pdf(empty_res_tree / "file.pdf")
    generate_test_files.create_json(empty_res_tree / "file.json")
    generate_test_files.create_yaml(empty_res_tree / "file.yaml")
    return empty_res_tree


@pytest.fixture
def res_tree_diff(empty_res_tree):
    """Result directory tree different from the reference."""
    generate_test_files.create_pdf(empty_res_tree / "file.pdf", diff=True)
    generate_test_files.create_json(empty_res_tree / "file.json", diff=True)
    generate_test_files.create_yaml(empty_res_tree / "file.yaml", diff=True)
    return empty_res_tree


@pytest.fixture
def pdf_diff():
    """The diff that should be reported for the PDF files."""
    return r"The files '\S*/file.pdf' and '\S*/file.pdf' are different\."


@pytest.fixture
def dict_diff():
    """The diff that should be reported for the JSON and YAML files."""
    diff = (
        r"""The files '\S*' and '\S*' are different:\n"""
        r"""Added the value\(s\) '{"#dict_key_2#": \[1, 2, 3\], "#dict_key_3#": \[1, 2, 3\], """
        r""""#dict_key_4#": \[1, 2, 3\]}' in the '\[simple_dict\]' key\.\n"""
        r"""Added the value\(s\) '{"#nested_dict_key_2#": "nested_dict_val_2", """
        r""""nested_dict_key_1": "#nested_dict_val_1#"}' in the '\[nested_dict\]"""
        r"""\[sub_nested_dict\]' key\.\n"""
        r"""Added the value\(s\) '{"#nested_dict_key_2#": "nested_dict_val_2"}' in the """
        r"""'\[nested_list\]\[3\]\[1\]' key\.\n"""
        r"""Added the value\(s\) '{"simple_list_test": \[\["dict_key_1", \[1, 4, 3\]\], """
        r"""\["#dict_key_2#", \[1, 2, 3\]\]\]}' in the '' key\.\n"""
        r"""Changed the value of '\[int_value\]' from 1 to 2\.\n"""
        r"""Changed the value of '\[nested_dict\]\[dict_key\]\[1\]' from 2 to 4\.\n"""
        r"""Changed the value of '\[nested_dict\]\[sub_nested_dict\]\[nested_list_key\]"""
        r"""\[0\]' from 1 to 2\.\n"""
        r"""Changed the value of '\[nested_dict\]\[sub_nested_dict\]\[nested_list_key\]"""
        r"""\[1\]' from 2.5 to 2.50001\.\n"""
        r"""Changed the value of '\[nested_dict\]\[sub_nested_dict\]\[nested_list_key\]"""
        r"""\[2\]' from 'str_val' to '#str_val#'\.\n"""
        r"""Changed the value of '\[nested_list\]\[0\]' from 1 to 2\.\n"""
        r"""Changed the value of '\[nested_list\]\[1\]' from 2.5 to 2.50001\.\n"""
        r"""Changed the value of '\[nested_list\]\[2\]' from 'str_val' to '#str_val#'\.\n"""
        r"""Changed the value of '\[nested_list\]\[3\]\[0\]' from 'nested_list_val' to """
        r"""'#nested_list_val#'\.\n"""
        r"""Changed the value of '\[nested_list\]\[3\]\[1\]\[nested_dict_key_1\]' from """
        r"""'nested_dict_val_1' to '#nested_dict_val_1#'\.\n"""
        r"""Changed the value of '\[nested_list\]\[3\]\[1\]\[nested_list_key\]\[0\]' from 1 """
        r"""to 2\.\n"""
        r"""Changed the value of '\[nested_list\]\[3\]\[1\]\[nested_list_key\]\[1\]' from """
        r"""2.5 to 2.50001\.\n"""
        r"""Changed the value of '\[nested_list\]\[3\]\[1\]\[nested_list_key\]\[2\]' from """
        r"""'str_val' to '#str_val#'\.\n"""
        r"""Changed the value of '\[simple_dict\]\[dict_key_1\]\[1\]' from 2 to 4\.\n"""
        r"""Changed the value of '\[simple_list\]\[0\]' from 1 to 2\.\n"""
        r"""Changed the value of '\[simple_list\]\[1\]' from 2.5 to 2.50001\.\n"""
        r"""Changed the value of '\[simple_list\]\[2\]' from 'str_val' to '#str_val#'\.\n"""
        r"""Removed the value\(s\) '{"dict_key_2": \[1, 2, 3\]}' from '\[simple_dict\]' """
        r"""key\.\n"""
        r"""Removed the value\(s\) '{"nested_dict_key": "nested_dict_val"}' from '\["""
        r"""nested_dict\]\[sub_nested_dict\]' key\.\n"""
        r"""Removed the value\(s\) '{"nested_dict_key_2": "nested_dict_val_2"}' from """
        r"""'\[nested_list\]\[3\]\[1\]' key\.\n"""
        r"""Removed the value\(s\) '{"nested_dict_test": 0}' from '' key\."""
    )
    return diff


@pytest.fixture
def registry_reseter():
    """Fixture to automatically reset the registry before and after a test."""
    dir_content_diff.reset_comparators()
    yield None
    dir_content_diff.reset_comparators()
