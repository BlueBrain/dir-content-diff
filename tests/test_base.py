"""Test the base features of the ``dir-content-diff`` package."""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=use-implicit-booleaness-not-comparison
import configparser
import copy
import json
import re

import dictdiffer
import pytest

import dir_content_diff
from dir_content_diff import assert_equal_trees
from dir_content_diff import compare_trees


class TestBaseComparator:
    """Test the base comparator."""

    def test_equal(self):
        """Test equal."""
        assert dir_content_diff.JsonComparator() != dir_content_diff.PdfComparator()
        assert dir_content_diff.JsonComparator() == dir_content_diff.JsonComparator()

        class ComparatorWithAttributes(dir_content_diff.base_comparators.BaseComparator):
            """Compare data from two JSON files."""

            def __init__(self, arg1, arg2):
                super().__init__()
                self.arg1 = arg1
                if arg2:
                    self.arg2 = arg2

            def diff(self, ref, comp, *args, **kwargs):
                return False

        assert ComparatorWithAttributes(1, 2) == ComparatorWithAttributes(1, 2)
        assert ComparatorWithAttributes(1, 2) != ComparatorWithAttributes(3, 4)
        assert ComparatorWithAttributes(1, 2) != ComparatorWithAttributes(1, None)

    def test_load_kwargs(self, ref_tree, res_tree_diff):
        """Test the load_kwargs method."""

        class ComparatorWithLoader(dir_content_diff.base_comparators.JsonComparator):
            """Compare data from two JSON files."""

            def load(self, path, load_empty=False):
                if load_empty:
                    return {}
                return super().load(path)

        ref_file = ref_tree / "file.json"
        res_file = res_tree_diff / "file.json"

        diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithLoader(),
        )

        no_load_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithLoader(),
            load_kwargs={"load_empty": False},
        )

        no_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithLoader(),
            load_kwargs={"load_empty": True},
        )

        no_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithLoader(default_load_kwargs={"load_empty": True}),
        )

        diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithLoader(default_load_kwargs={"load_empty": True}),
            load_kwargs={"load_empty": False},
        )

        kwargs_msg = "Kwargs used for loading data: {'load_empty': False}\n"
        assert kwargs_msg in no_load_diff
        assert diff == no_load_diff.replace(kwargs_msg, "")
        assert diff is not False
        assert no_diff is False
        assert no_diff_default is False
        assert kwargs_msg in diff_default
        assert diff_default.replace(kwargs_msg, "") == diff

    def test_filter_kwargs(self, ref_tree, res_tree_diff):
        """Test the filter_kwargs method."""

        class ComparatorWithFilter(dir_content_diff.base_comparators.JsonComparator):
            """Compare data from two JSON files."""

            def filter(self, differences, remove_all=False):
                if remove_all:
                    return []
                return differences

        ref_file = ref_tree / "file.json"
        res_file = res_tree_diff / "file.json"

        diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFilter(),
        )

        no_filter_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFilter(),
            filter_kwargs={"remove_all": False},
        )

        no_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFilter(),
            filter_kwargs={"remove_all": True},
        )

        no_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFilter(default_filter_kwargs={"remove_all": True}),
        )

        diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFilter(default_filter_kwargs={"remove_all": True}),
            filter_kwargs={"remove_all": False},
        )

        kwargs_msg = "Kwargs used for filtering differences: {'remove_all': False}\n"
        assert kwargs_msg in no_filter_diff
        assert diff == no_filter_diff.replace(kwargs_msg, "")
        assert diff is not False
        assert no_diff is False
        assert no_diff_default is False
        assert kwargs_msg in diff_default
        assert diff_default.replace(kwargs_msg, "") == diff

    def test_format_kwargs(self, ref_tree, res_tree_diff):
        """Test the format_kwargs method."""

        class ComparatorWithFormat(dir_content_diff.base_comparators.JsonComparator):
            """Compare data from two JSON files."""

            def format_diff(self, difference, mark_formatted=False):
                """Format one element difference."""
                difference = super().format_diff(difference)
                if mark_formatted:
                    difference += "### FORMATTED"
                return difference

        ref_file = ref_tree / "file.json"
        res_file = res_tree_diff / "file.json"

        diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFormat(),
        )

        no_format_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFormat(),
            format_diff_kwargs={"mark_formatted": False},
        )

        formatted_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFormat(),
            format_diff_kwargs={"mark_formatted": True},
        )

        formatted_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFormat(default_format_diff_kwargs={"mark_formatted": True}),
        )

        diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFormat(default_format_diff_kwargs={"mark_formatted": True}),
            format_diff_kwargs={"mark_formatted": False},
        )

        kwargs_msg = "Kwargs used for formatting differences: {'mark_formatted': False}\n"
        assert kwargs_msg in no_format_diff
        assert diff == no_format_diff.replace(kwargs_msg, "")
        assert len(re.findall("### FORMATTED", diff)) == 0
        assert len(re.findall("### FORMATTED", formatted_diff)) == 25
        assert len(re.findall("### FORMATTED", formatted_diff_default)) == 25
        assert kwargs_msg in diff_default
        assert diff_default.replace(kwargs_msg, "") == diff

    def test_sort_kwargs(self, ref_tree, res_tree_diff):
        """Test the sort_kwargs method."""

        class ComparatorWithSort(dir_content_diff.base_comparators.JsonComparator):
            """Compare data from two JSON files."""

            def sort(self, differences, reverse=False):
                """Sort the element differences."""
                return sorted(differences, reverse=reverse)

        ref_file = ref_tree / "file.json"
        res_file = res_tree_diff / "file.json"

        diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithSort(),
        )

        no_reversed_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithSort(),
            sort_kwargs={"reverse": False},
        )

        reversed_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithSort(),
            sort_kwargs={"reverse": True},
        )

        reversed_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithSort(default_sort_kwargs={"reverse": True}),
        )

        no_reversed_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithSort(default_sort_kwargs={"reverse": True}),
            sort_kwargs={"reverse": False},
        )

        kwargs_msg = "Kwargs used for sorting differences: {'reverse': True}\n"
        kwargs_msg_false = kwargs_msg.replace("True", "False")
        expected_reversed_diff = "\n".join(
            diff.split("\n")[:1] + sorted(diff.split("\n")[1:], reverse=True)
        )

        assert kwargs_msg not in diff
        assert kwargs_msg_false not in diff
        assert kwargs_msg_false in no_reversed_diff
        assert kwargs_msg in reversed_diff
        assert kwargs_msg in reversed_diff_default
        assert kwargs_msg_false in no_reversed_diff_default

        assert diff == no_reversed_diff.replace(kwargs_msg_false, "")
        assert expected_reversed_diff == reversed_diff.replace(kwargs_msg, "")
        assert expected_reversed_diff == reversed_diff_default.replace(kwargs_msg, "")
        assert diff == no_reversed_diff_default.replace(kwargs_msg_false, "")

    def test_concat_kwargs(self, ref_tree, res_tree_diff):
        """Test the concat_kwargs method."""

        class ComparatorWithConcat(dir_content_diff.base_comparators.JsonComparator):
            """Compare data from two JSON files."""

            def concatenate(self, differences, eol=None):
                """Concatenate the differences."""
                if not eol:
                    eol = "\n"
                return eol.join(differences)

        ref_file = ref_tree / "file.json"
        res_file = res_tree_diff / "file.json"

        diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithConcat(),
        )

        concat_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithConcat(),
            concat_kwargs={"eol": "\n"},
        )

        concat_eol_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithConcat(),
            concat_kwargs={"eol": "#EOL#"},
        )

        concat_eol_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithConcat(default_concat_kwargs={"eol": "#EOL#"}),
        )

        concat_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithConcat(default_concat_kwargs={"eol": "#EOL#"}),
            concat_kwargs={"eol": "\n"},
        )

        kwargs_msg_eol = "\nKwargs used for concatenating differences: {'eol': '#EOL#'}\n"
        kwargs_msg_n = kwargs_msg_eol.replace("#EOL#", "\\n")
        TEST_EOL = "__TEST_EOL__"

        assert kwargs_msg_eol not in diff
        assert kwargs_msg_n not in diff
        assert kwargs_msg_n in concat_diff
        assert kwargs_msg_eol in concat_eol_diff
        assert kwargs_msg_eol in concat_eol_diff_default
        assert kwargs_msg_n in concat_diff_default

        assert diff == concat_diff.replace(kwargs_msg_n, "\n")
        assert concat_diff.replace(kwargs_msg_n, "").replace(
            "\n", TEST_EOL
        ) == concat_eol_diff.replace(kwargs_msg_eol, "").replace("#EOL#", TEST_EOL)
        assert concat_eol_diff == concat_eol_diff_default
        assert diff == concat_diff_default.replace(kwargs_msg_n, "\n")

    def test_report_kwargs(self, ref_tree, res_tree_diff):
        """Test the report_kwargs method."""

        class ComparatorWithReport(dir_content_diff.base_comparators.JsonComparator):
            """Compare data from two JSON files."""

            def report(
                self,
                ref_file,
                comp_file,
                formatted_differences,
                diff_args,
                diff_kwargs,
                mark_report=None,
                **kwargs,
            ):
                if mark_report is not None:
                    kwargs["mark_report"] = mark_report
                report = super().report(
                    ref_file, comp_file, formatted_differences, diff_args, diff_kwargs, **kwargs
                )
                if mark_report:
                    report += "### REPORTED"
                return report

        ref_file = ref_tree / "file.json"
        res_file = res_tree_diff / "file.json"

        diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithReport(),
        )

        no_report_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithReport(),
            report_kwargs={"mark_report": False},
        )

        reported_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithReport(),
            report_kwargs={"mark_report": True},
        )

        reported_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithReport(default_report_kwargs={"mark_report": True}),
        )

        no_report_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithReport(default_report_kwargs={"mark_report": True}),
            report_kwargs={"mark_report": False},
        )

        kwargs_msg = "Kwargs used for reporting differences: {'mark_report': False}\n"
        assert kwargs_msg in no_report_diff
        assert diff == no_report_diff.replace(kwargs_msg, "")
        assert len(re.findall("### REPORTED", diff)) == 0
        assert len(re.findall("### REPORTED", reported_diff)) == 1
        assert len(re.findall("### REPORTED", reported_diff_default)) == 1
        assert kwargs_msg in no_report_diff_default
        assert no_report_diff_default.replace(kwargs_msg, "") == diff

    class TestJsonComparator:
        """Test the JSON comparator."""

        def test_format_data(self):
            """Test data formatting."""
            data = {
                "a": 1,
                "b": {
                    "c": "a string",
                },
                "d": [
                    {"d1": "the d1 string"},
                    {"d2": "the d2 string"},
                ],
                "e": {
                    "nested_e": {
                        "nested_e_a": "the nested_e_a string",
                        "nested_e_b": "the nested_e_b string",
                    }
                },
            }
            initial_data = copy.deepcopy(data)

            expected_data = {
                "a": 1,
                "b": {
                    "c": "a NEW VALUE",
                },
                "d": [
                    {"d1": "the d1 NEW VALUE"},
                    {"d2": "the d2 NEW VALUE"},
                ],
                "e": {
                    "nested_e": {
                        "nested_e_a": "the nested_e_a NEW VALUE",
                        "nested_e_b": "the nested_e_b NEW VALUE",
                    }
                },
            }

            patterns = {
                ("string", "NEW VALUE"): [
                    "b.c",
                    "d[*].*",
                    "e.*.*",
                ]
            }

            comparator = dir_content_diff.JsonComparator()
            comparator.format_data(data)
            assert data == initial_data

            data = copy.deepcopy(initial_data)
            comparator = dir_content_diff.JsonComparator()
            comparator.format_data(data, replace_pattern=patterns)
            assert data == expected_data

            # Missing key in ref
            comparator = dir_content_diff.JsonComparator()
            data = copy.deepcopy(initial_data)
            ref = {"a": 1}
            comparator.format_data(data, ref, replace_pattern=patterns)
            assert data == initial_data
            assert comparator.current_state["format_errors"] == [
                ("missing_ref_entry", i, None) for i in patterns[("string", "NEW VALUE")]
            ]

            # Missing key in data
            comparator = dir_content_diff.JsonComparator()
            ref = copy.deepcopy(initial_data)
            data = {"a": 1}
            comparator.format_data(data, ref, replace_pattern=patterns)
            assert data == {"a": 1}
            assert comparator.current_state["format_errors"] == [
                ("missing_comp_entry", i, None) for i in patterns[("string", "NEW VALUE")]
            ]

    class TestXmlComparator:
        """Test the XML comparator."""

        def test_xmltodict(self):
            """Test all types of the xmltodict auto cast feature."""
            comparator = dir_content_diff.XmlComparator()

            # Test empty root
            res = comparator.xmltodict(
                # fmt: off
                """<?xml version="1.0" encoding="UTF-8" ?>"""
                """<root>"""
                """</root>"""
                # fmt: on
            )
            assert res == {"root": {}}

            # Test all types
            res = comparator.xmltodict(
                """<?xml version="1.0" encoding="UTF-8" ?>"""
                """<root>"""
                """    <str_value_no_type>a str value</str_value_no_type>"""
                """    <str_value type="str">another str value</str_value>"""
                """    <int_value type="int">1</int_value>"""
                """    <float_value type="float">1.5</float_value>"""
                """    <boolean_true type="bool">TrUe</boolean_true>"""
                """    <boolean_false type="bool">FaLsE</boolean_false>"""
                """    <simple_list type="list">"""
                """        <item type="int">1</item>"""
                """        <item type="float">2.5</item>"""
                """        <item type="str">str_val</item>"""
                """    </simple_list>"""
                """    <simple_dict type="dict">"""
                """        <key_1 type="int">1</key_1>"""
                """        <key_2 type="float">2.5</key_2>"""
                """        <key_3 type="str">str_val</key_3>"""
                """        <key_4>another str val</key_4>"""
                """    </simple_dict>"""
                """    <none type="null">any thing here is not considered</none>"""
                """</root>"""
            )
            assert res["root"]["none"] is None
            del res["root"]["none"]
            assert res == {
                "root": {
                    "str_value_no_type": "a str value",
                    "str_value": "another str value",
                    "int_value": 1,
                    "float_value": 1.5,
                    "boolean_true": True,
                    "boolean_false": False,
                    "simple_list": [1, 2.5, "str_val"],
                    "simple_dict": {
                        "key_1": 1,
                        "key_2": 2.5,
                        "key_3": "str_val",
                        "key_4": "another str val",
                    },
                }
            }

            # Test unknown type
            with pytest.raises(TypeError, match=r"Unsupported type.*"):
                comparator.xmltodict(
                    """<?xml version="1.0" encoding="UTF-8" ?>"""
                    """<root>"""
                    """    <bad_type type="UNKNOWN TYPE">1</bad_type>"""
                    """</root>"""
                )

            # Test bad value in boolean
            with pytest.raises(ValueError, match="Bool attributes expect 'true' or 'false'."):
                comparator.xmltodict(
                    """<?xml version="1.0" encoding="UTF-8" ?>"""
                    """<root>"""
                    """    <bad_bool type="bool">not a bool</bad_bool>"""
                    """</root>"""
                )

        def test_add_to_output_with_none(self):
            """Test wrong type for add_to_output() method."""
            comparator = dir_content_diff.XmlComparator()
            comparator.add_to_output(None, None)

    class TestIniComparator:
        """Test the INI comparator."""

        def test_initodict(self, ref_tree):
            """Test conversion of INI files into dict."""
            data = configparser.ConfigParser()
            data.read(ref_tree / "file.ini")

            comparator = dir_content_diff.IniComparator()
            res = comparator.configparser_to_dict(data)
            assert res == {
                "section1": {"attr1": "val1", "attr2": 1},
                "section2": {"attr3": [1, 2, "a", "b"], "attr4": {"a": 1, "b": [1, 2]}},
            }


class TestRegistry:
    """Test the internal registry."""

    def test_init_register(self, registry_reseter):
        """Test the initial registry with the get_comparators() function."""
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".cfg": dir_content_diff.IniComparator(),
            ".conf": dir_content_diff.IniComparator(),
            ".ini": dir_content_diff.IniComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".xml": dir_content_diff.XmlComparator(),
        }

    def test_update_register(self, registry_reseter):
        """Test the functions to update the registry."""
        dir_content_diff.register_comparator(".test_ext", dir_content_diff.JsonComparator())
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".cfg": dir_content_diff.IniComparator(),
            ".conf": dir_content_diff.IniComparator(),
            ".ini": dir_content_diff.IniComparator(),
            ".test_ext": dir_content_diff.JsonComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".xml": dir_content_diff.XmlComparator(),
        }

        dir_content_diff.unregister_comparator(".yaml")
        dir_content_diff.unregister_comparator("json")  # Test suffix without dot
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".cfg": dir_content_diff.IniComparator(),
            ".conf": dir_content_diff.IniComparator(),
            ".ini": dir_content_diff.IniComparator(),
            ".test_ext": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".xml": dir_content_diff.XmlComparator(),
        }

        dir_content_diff.reset_comparators()
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".cfg": dir_content_diff.IniComparator(),
            ".conf": dir_content_diff.IniComparator(),
            ".ini": dir_content_diff.IniComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".xml": dir_content_diff.XmlComparator(),
        }

        with pytest.raises(
            ValueError,
            match=(
                "The '.pdf' extension is already registered and must be unregistered before being "
                "replaced."
            ),
        ):
            dir_content_diff.register_comparator(".pdf", dir_content_diff.JsonComparator())

        with pytest.raises(ValueError, match="The '.unknown_ext' extension is not registered."):
            dir_content_diff.unregister_comparator(".unknown_ext")

        dir_content_diff.unregister_comparator(".unknown_ext", quiet=True)
        dir_content_diff.register_comparator(".new_ext", dir_content_diff.JsonComparator())
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".cfg": dir_content_diff.IniComparator(),
            ".conf": dir_content_diff.IniComparator(),
            ".ini": dir_content_diff.IniComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".xml": dir_content_diff.XmlComparator(),
            ".new_ext": dir_content_diff.JsonComparator(),
        }
        dir_content_diff.register_comparator(
            ".new_ext", dir_content_diff.PdfComparator(), force=True
        )
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".cfg": dir_content_diff.IniComparator(),
            ".conf": dir_content_diff.IniComparator(),
            ".ini": dir_content_diff.IniComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".xml": dir_content_diff.XmlComparator(),
            ".new_ext": dir_content_diff.PdfComparator(),
        }


@pytest.fixture
def ref_with_nested_file(ref_tree):
    """Update the ref tree to have nesteed files."""
    ref_pdf_file = ref_tree / "file.pdf"
    new_ref_pdf_file = ref_tree / "level1" / "level2" / "level3" / "file.pdf"
    new_ref_pdf_file.parent.mkdir(parents=True)
    ref_pdf_file.rename(new_ref_pdf_file)
    return ref_tree


@pytest.fixture
def res_equal_with_nested_file(res_tree_equal):
    """Update the result tree to have nesteed files."""
    res_pdf_file = res_tree_equal / "file.pdf"
    new_res_pdf_file = res_tree_equal / "level1" / "level2" / "level3" / "file.pdf"
    new_res_pdf_file.parent.mkdir(parents=True)
    res_pdf_file.rename(new_res_pdf_file)
    return res_tree_equal


@pytest.fixture
def res_diff_with_nested_file(res_tree_diff):
    """Update the result tree to have nesteed files."""
    res_pdf_file = res_tree_diff / "file.pdf"
    new_res_pdf_file = res_tree_diff / "level1" / "level2" / "level3" / "file.pdf"
    new_res_pdf_file.parent.mkdir(parents=True)
    res_pdf_file.rename(new_res_pdf_file)
    return res_tree_diff


class TestEqualTrees:
    """Tests that should return no difference."""

    def test_diff_tree(self, ref_tree, res_tree_equal):
        """Test that no difference is returned."""
        res = compare_trees(ref_tree, res_tree_equal)
        assert res == {}

    def test_assert_equal_trees(self, ref_tree, res_tree_equal):
        """Test that no exception is raised."""
        assert_equal_trees(ref_tree, res_tree_equal)

    def test_assert_equal_trees_export(self, ref_tree, res_tree_equal):
        """Test that the formatted files are properly exported."""
        assert_equal_trees(
            ref_tree,
            res_tree_equal,
            export_formatted_files=True,
        )
        assert sorted(res_tree_equal.with_name(res_tree_equal.name + "_FORMATTED").iterdir()) == [
            (res_tree_equal.with_name(res_tree_equal.name + "_FORMATTED") / "file").with_suffix(
                suffix
            )
            for suffix in [".ini", ".json", ".xml", ".yaml"]
        ]

    def test_diff_empty(self, empty_ref_tree, empty_res_tree):
        """Test with empty trees."""
        res = compare_trees(empty_ref_tree, empty_res_tree)
        assert res == {}

    def test_pass_register(self, empty_ref_tree, empty_res_tree):
        """Test with empty trees and with an explicit set of comparators."""
        res = compare_trees(
            empty_ref_tree, empty_res_tree, comparators=dir_content_diff.get_comparators()
        )
        assert res == {}

    def test_unknown_comparator(self, ref_tree, res_tree_equal, registry_reseter):
        """Test with an unknown extension."""
        dir_content_diff.unregister_comparator(".yaml")
        res = compare_trees(ref_tree, res_tree_equal)
        assert res == {}

    def test_nested_files(self, ref_with_nested_file, res_equal_with_nested_file):
        """Test with nested files."""
        res = compare_trees(ref_with_nested_file, res_equal_with_nested_file)
        assert res == {}

    def test_specific_args(self, ref_tree, res_tree_equal):
        """Test specific args."""
        specific_args = {
            "file.yaml": {"args": [None, None, None, False, 0, False]},
            "file.json": {"tolerance": 0},
        }
        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert res == {}

    def test_replace_pattern(self, ref_tree, res_tree_equal):
        """Test specific args."""
        specific_args = {
            "file.yaml": {"args": [None, None, None, False, 0, False]},
            "file.json": {
                "format_data_kwargs": {
                    "replace_pattern": {(".*val.*", "NEW_VAL"): ["*.[*]"]},
                },
            },
        }
        res = compare_trees(
            ref_tree, res_tree_equal, specific_args=specific_args, export_formatted_files=True
        )

        pat = (
            r"""The files '\S*/ref/file\.json' and '\S*/res/file\.json' are different:\n"""
            r"""Kwargs used for formatting data: """
            r"""{'replace_pattern': {\('\.\*val\.\*', 'NEW_VAL'\): \['\*\.\[\*\]'\]}}\n"""
            r"""Changed the value of '\[nested_list\]\[2\]' from 'str_val' to 'NEW_VAL'\.\n"""
            r"""Changed the value of '\[simple_list\]\[2\]' from 'str_val' to 'NEW_VAL'\."""
        )

        assert re.match(pat, res["file.json"]) is not None

    def test_specific_comparator(self, ref_tree, res_tree_equal):
        """Test specific args."""
        specific_args = {
            "file.yaml": {"args": [None, None, None, False, 0, False]},
            "file.json": {"comparator": dir_content_diff.DefaultComparator()},
        }
        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert res == {}

    def test_specific_patterns(self, ref_tree, res_tree_equal, base_diff):
        """Test specific args."""
        specific_args = {
            "all yaml files": {
                "args": [None, None, None, False, 0, False],
                "patterns": [r".*\.yaml"],
            },
            "all json files": {
                "comparator": dir_content_diff.DefaultComparator(),
                "patterns": [r".*\.json"],
            },
        }
        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert res == {}

        # Test pattern override
        specific_args["all json files"]["comparator"] = dir_content_diff.PdfComparator()
        specific_args["file.json"] = {"comparator": dir_content_diff.DefaultComparator()}
        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert res == {}

        # Test pattern multiple matches
        specific_args = {
            "all files": {
                "comparator": dir_content_diff.DefaultComparator(),
                "patterns": [r"file\..*"],
            },
        }
        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert list(res.keys()) == ["file.pdf"]
        assert re.match(base_diff, res["file.pdf"]) is not None


class TestDiffTrees:
    """Tests that should return differences."""

    def test_diff_tree(self, ref_tree, res_tree_diff, pdf_diff, dict_diff, xml_diff, ini_diff):
        """Test that the returned differences are correct."""
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 5
        match_res_0 = re.match(pdf_diff, res["file.pdf"])
        match_res_1 = re.match(dict_diff, res["file.json"])
        match_res_2 = re.match(dict_diff, res["file.yaml"])
        match_res_3 = re.match(xml_diff, res["file.xml"])
        match_res_4 = re.match(ini_diff, res["file.ini"])

        for match_i in [match_res_0, match_res_1, match_res_2, match_res_3, match_res_4]:
            assert match_i is not None

    def test_assert_equal_trees(self, ref_tree, res_tree_diff, pdf_diff, dict_diff, xml_diff):
        """Test that the exception raised is correct."""
        pattern = (r"\n\n\n").join([dict_diff, pdf_diff, xml_diff, dict_diff])
        with pytest.raises(AssertionError, match=pattern):
            assert_equal_trees(ref_tree, res_tree_diff)

    def test_diff_ref_empty_res_not_empty(self, empty_ref_tree, res_tree_equal):
        """Test with empty ref tree."""
        res = compare_trees(empty_ref_tree, res_tree_equal)
        assert res == {}

    def test_diff_ref_not_empty_res_empty(self, ref_tree, empty_res_tree):
        """Test with empty compared tree."""
        res = compare_trees(ref_tree, empty_res_tree)

        assert len(res) == 5
        match_res_0 = re.match(
            r"The file 'file.pdf' does not exist in '\S*/res'\.", res["file.pdf"]
        )
        match_res_1 = re.match(
            r"The file 'file.yaml' does not exist in '\S*/res'\.", res["file.yaml"]
        )
        match_res_2 = re.match(
            r"The file 'file.json' does not exist in '\S*/res'\.", res["file.json"]
        )
        match_res_3 = re.match(
            r"The file 'file.xml' does not exist in '\S*/res'\.", res["file.xml"]
        )
        match_res_4 = re.match(
            r"The file 'file.ini' does not exist in '\S*/res'\.", res["file.ini"]
        )

        for match_i in [match_res_0, match_res_1, match_res_2, match_res_3, match_res_4]:
            assert match_i is not None

    def test_exception_in_comparator(self, ref_tree, res_tree_equal, registry_reseter):
        """Test with a comparator raising an exception."""

        def bad_comparator(ref_path, test_path, *args, **kwargs):
            raise RuntimeError("Bad\ncomparator")

        dir_content_diff.unregister_comparator(".yaml")
        dir_content_diff.register_comparator(".yaml", bad_comparator)

        res = compare_trees(ref_tree, res_tree_equal)

        assert len(res) == 1
        match = re.match(
            r"The files '\S*/ref/file\.yaml' and '\S*/res/file\.yaml' are different:\n"
            r"Exception raised: \(RuntimeError\) Bad\ncomparator",
            res["file.yaml"],
        )
        assert match is not None

        def bad_comparator_no_str(ref_path, test_path, *args, **kwargs):
            raise RuntimeError((1, ("Bad\ncomparator", 2)))

        dir_content_diff.unregister_comparator(".yaml")
        dir_content_diff.register_comparator(".yaml", bad_comparator_no_str)

        res = compare_trees(ref_tree, res_tree_equal)

        assert len(res) == 1
        match = re.match(
            r"The files '\S*/ref/file\.yaml' and '\S*/res/file\.yaml' are different:\n"
            r"Exception raised: \(RuntimeError\) \(1, \('Bad\\ncomparator', 2\)\)",
            res["file.yaml"],
        )
        assert match is not None

        class NoRepr:
            """A class to test exception handling failure."""

            def __repr__(self):
                raise ValueError("This object can not be represented")

        def bad_comparator_exception_failing(ref_path, test_path, *args, **kwargs):
            raise RuntimeError((NoRepr(), ("Bad\ncomparator", NoRepr())))

        dir_content_diff.unregister_comparator(".yaml")
        dir_content_diff.register_comparator(".yaml", bad_comparator_exception_failing)

        res = compare_trees(ref_tree, res_tree_equal)

        assert len(res) == 1
        match = re.match(
            r"The files '\S*/ref/file\.yaml' and '\S*/res/file\.yaml' are different:\n"
            r"Exception raised: \(RuntimeError\) UNKNOWN ERROR: Could not get information from "
            r"the exception",
            res["file.yaml"],
        )
        assert match is not None

    def test_specific_args(self, ref_tree, res_tree_diff, dict_diff, xml_diff, ini_diff):
        """Test specific args."""
        specific_args = {
            "file.pdf": {"threshold": 50},
            "file.json": {"tolerance": 0},
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        # This time the PDF files are considered as equal
        assert len(res) == 4
        match_res_0 = re.match(dict_diff, res["file.yaml"])
        match_res_1 = re.match(
            dict_diff.replace(
                r"are different:\n",
                r"are different:\nKwargs used for computing differences: \{'tolerance': 0\}\n",
            ),
            res["file.json"],
        )
        match_res_2 = re.match(xml_diff, res["file.xml"])
        match_res_3 = re.match(ini_diff, res["file.ini"])

        for match_i in [match_res_0, match_res_1, match_res_2, match_res_3]:
            assert match_i is not None

    def test_specific_patterns(self, ref_tree, res_tree_diff, base_diff, dict_diff):
        """Test specific args."""
        specific_args = {
            "all yaml files": {
                "args": [None, None, None, False, 0, False],
                "patterns": [r".*\.yaml"],
            },
            "all json files": {
                "comparator": dir_content_diff.DefaultComparator(),
                "patterns": [r".*\.json"],
            },
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert re.match(base_diff, res["file.json"]) is not None

        # Test pattern override
        specific_args["all json files"]["comparator"] = dir_content_diff.DefaultComparator()
        specific_args["file.json"] = {"comparator": dir_content_diff.JsonComparator()}
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert re.match(dict_diff, res["file.json"]) is not None

        # Test pattern multiple matches
        specific_args = {
            "all files": {
                "comparator": dir_content_diff.DefaultComparator(),
                "patterns": [r"file\..*"],
            },
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert sorted(res.keys()) == [
            "file.ini",
            "file.json",
            "file.pdf",
            "file.xml",
            "file.yaml",
        ]
        for v in res.values():
            assert re.match(base_diff, v)

    def test_unknown_comparator(self, ref_tree, res_tree_diff, registry_reseter):
        """Test with an unknown extension."""
        dir_content_diff.unregister_comparator(".yaml")
        res = compare_trees(ref_tree, res_tree_diff)
        match = re.match(
            r"The files '\S*/ref/file\.yaml' and '\S*/res/file\.yaml' are different.",
            res["file.yaml"],
        )
        assert match is not None

    def test_nested_files(self, ref_with_nested_file, res_diff_with_nested_file):
        """Test with nested files."""
        res = compare_trees(ref_with_nested_file, res_diff_with_nested_file)
        match = re.match(
            r"The files '\S*/ref/level1/level2/level3/file\.pdf' and "
            r"'\S*/res/level1/level2/level3/file\.pdf' are different\.",
            res["level1/level2/level3/file.pdf"],
        )
        assert match is not None

    def test_fix_dot_notation(
        self, ref_tree, res_tree_diff, pdf_diff, dict_diff, xml_diff, ini_diff
    ):
        """Test that the dot notation is properly fixed."""
        specific_args = {"file.yaml": {"args": [None, None, None, False, 0, True]}}
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert len(res) == 5
        match_res_0 = re.match(pdf_diff, res["file.pdf"])
        match_res_1 = re.match(
            dict_diff.replace(
                r"are different:\n",
                r"are different:\nArgs used for computing differences: "
                r"\[None, None, None, False, 0, True\]\n",
            ),
            res["file.yaml"],
        )
        match_res_2 = re.match(dict_diff, res["file.json"])
        match_res_3 = re.match(xml_diff, res["file.xml"])
        match_res_4 = re.match(ini_diff, res["file.ini"])

        for match_i in [match_res_0, match_res_1, match_res_2, match_res_3, match_res_4]:
            assert match_i is not None

    def test_format_inside_diff(self, ref_tree, res_tree_diff, dict_diff):
        """Test formatting the result inside the diff method."""

        class JsonComparator(dir_content_diff.base_comparators.BaseComparator):
            """Compare data from two JSON files."""

            def load(self, path, *args, **kwargs):
                with open(path) as file:  # pylint: disable=unspecified-encoding
                    data = json.load(file)
                return data

            def diff(self, ref, comp, *args, **kwargs):
                diffs = list(dictdiffer.diff(ref, comp, *args, dot_notation=False, **kwargs))

                # Format here instead of overriding the default format method
                comparator = dir_content_diff.base_comparators.JsonComparator()
                formatted = [comparator.format_diff(i) for i in diffs]

                return formatted

        res = compare_trees(ref_tree, res_tree_diff, comparators={".json": JsonComparator()})

        match = re.match(dict_diff, res["file.json"])

        assert match is not None


class TestProgrammaticUse:
    """Test specific comparators that could be use programmatically."""

    def test_diff_tree(self, ref_tree, res_tree_diff, pdf_diff, dict_diff):
        """Test with different trees."""
        res = compare_trees(ref_tree, res_tree_diff, return_raw_diffs=True)

        res_json = res["file.json"]

        assert len(res_json) == 25
        assert len(list(filter(lambda x: x[0] == "change", res_json))) == 17
        assert len(list(filter(lambda x: x[0] == "add", res_json))) == 4
        assert len(list(filter(lambda x: x[0] == "remove", res_json))) == 4
