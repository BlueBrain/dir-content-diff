"""Test the base features of the dir-content-diff package."""
# pylint: disable=missing-function-docstring
# pylint: disable=no-self-use
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
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

        assert diff == no_load_diff
        assert diff is not False
        assert no_diff is False
        assert no_diff_default is False
        assert diff_default == diff

    def test_filter_kwargs(self, ref_tree, res_tree_diff):
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

        assert diff == no_filter_diff
        assert diff is not False
        assert no_diff is False
        assert no_diff_default is False
        assert diff_default == diff

    def test_format_kwargs(self, ref_tree, res_tree_diff):
        class ComparatorWithFormat(dir_content_diff.base_comparators.JsonComparator):
            """Compare data from two JSON files."""

            def format(self, difference, mark_formatted=False):
                """Format one element difference."""
                difference = super().format(difference)
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
            format_kwargs={"mark_formatted": False},
        )

        formatted_diff = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFormat(),
            format_kwargs={"mark_formatted": True},
        )

        formatted_diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFormat(default_format_kwargs={"mark_formatted": True}),
        )

        diff_default = dir_content_diff.compare_files(
            ref_file,
            res_file,
            ComparatorWithFormat(default_format_kwargs={"mark_formatted": True}),
            format_kwargs={"mark_formatted": False},
        )

        assert diff == no_format_diff
        assert len(re.findall("### FORMATTED", diff)) == 0
        assert len(re.findall("### FORMATTED", formatted_diff)) == 25
        assert len(re.findall("### FORMATTED", formatted_diff_default)) == 25
        assert diff_default == diff

    def test_report_kwargs(self, ref_tree, res_tree_diff):
        class ComparatorWithReport(dir_content_diff.base_comparators.JsonComparator):
            """Compare data from two JSON files."""

            def report(
                self,
                ref_file,
                comp_file,
                formatted_differences,
                diff_args,
                diff_kwargs,
                mark_report=False,
            ):
                report = super().report(
                    ref_file,
                    comp_file,
                    formatted_differences,
                    diff_args,
                    diff_kwargs,
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

        assert diff == no_report_diff
        assert len(re.findall("### REPORTED", diff)) == 0
        assert len(re.findall("### REPORTED", reported_diff)) == 1
        assert len(re.findall("### REPORTED", reported_diff_default)) == 1
        assert no_report_diff_default == diff

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
            """Test wront type for add_to_output() method."""
            comparator = dir_content_diff.XmlComparator()
            comparator.add_to_output(None, None)


class TestRegistry:
    """Test the internal registry."""

    def test_init_register(self, registry_reseter):
        """Test the initial registry with the get_comparators() function."""
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
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
            ".test_ext": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".xml": dir_content_diff.XmlComparator(),
        }

        dir_content_diff.reset_comparators()
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
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

        with pytest.raises(ValueError, match=("The '.unknown_ext' extension is not registered.")):
            dir_content_diff.unregister_comparator(".unknown_ext")

        dir_content_diff.unregister_comparator(".unknown_ext", quiet=True)
        dir_content_diff.register_comparator(".new_ext", dir_content_diff.JsonComparator())
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
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
        res = compare_trees(ref_tree, res_tree_equal)
        assert res == {}

    def test_assert_equal_trees(self, ref_tree, res_tree_equal):
        assert_equal_trees(ref_tree, res_tree_equal)

    def test_diff_empty(self, empty_ref_tree, empty_res_tree):
        res = compare_trees(empty_ref_tree, empty_res_tree)
        assert res == {}

    def test_pass_register(self, empty_ref_tree, empty_res_tree):
        res = compare_trees(
            empty_ref_tree, empty_res_tree, comparators=dir_content_diff.get_comparators()
        )
        assert res == {}

    def test_unknown_comparator(self, ref_tree, res_tree_equal, registry_reseter):
        dir_content_diff.unregister_comparator(".yaml")
        res = compare_trees(ref_tree, res_tree_equal)
        assert res == {}

    def test_nested_files(self, ref_with_nested_file, res_equal_with_nested_file):
        res = compare_trees(ref_with_nested_file, res_equal_with_nested_file)
        assert res == {}

    def test_specific_args(self, ref_tree, res_tree_equal):
        specific_args = {
            "file.yaml": {"args": [None, None, None, False, 0, False]},
            "file.json": {"kwargs": {"tolerance": 0}},
        }
        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert res == {}


class TestDiffTrees:
    """Tests that should return differences."""

    def test_diff_tree(self, ref_tree, res_tree_diff, pdf_diff, dict_diff, xml_diff):
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 4
        match_res_0 = re.match(pdf_diff, res["file.pdf"])
        match_res_1 = re.match(dict_diff, res["file.json"])
        match_res_2 = re.match(dict_diff, res["file.yaml"])
        match_res_3 = re.match(xml_diff, res["file.xml"])

        for match_i in [match_res_0, match_res_1, match_res_2, match_res_3]:
            assert match_i is not None

    def test_assert_equal_trees(self, ref_tree, res_tree_diff, pdf_diff, dict_diff, xml_diff):
        pattern = (r"\n\n\n").join([dict_diff, pdf_diff, xml_diff, dict_diff])
        with pytest.raises(AssertionError, match=pattern):
            assert_equal_trees(ref_tree, res_tree_diff)

    def test_diff_ref_empty_res_not_empty(self, empty_ref_tree, res_tree_equal):
        res = compare_trees(empty_ref_tree, res_tree_equal)
        assert res == {}

    def test_diff_ref_not_empty_res_empty(self, ref_tree, empty_res_tree):
        res = compare_trees(ref_tree, empty_res_tree)

        assert len(res) == 4
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

        for match_i in [match_res_0, match_res_1, match_res_2, match_res_3]:
            assert match_i is not None

    def test_exception_in_comparator(self, ref_tree, res_tree_equal, registry_reseter):
        def bad_comparator(ref_path, test_path, *args, **kwargs):
            raise RuntimeError("Bad\ncomparator")

        dir_content_diff.unregister_comparator(".yaml")
        dir_content_diff.register_comparator(".yaml", bad_comparator)

        res = compare_trees(ref_tree, res_tree_equal)

        assert len(res) == 1
        match = re.match(
            r"The files '\S*/ref/file.yaml' and '\S*/res/file.yaml' are different:\n"
            r"Exception raised: Bad\ncomparator",
            res["file.yaml"],
        )
        assert match is not None

    def test_specific_args(self, ref_tree, res_tree_diff, dict_diff, xml_diff):
        specific_args = {
            "file.pdf": {"kwargs": {"threshold": 50}},
            "file.json": {"kwargs": {"tolerance": 0}},
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        # This time the PDF files are considered as equal
        assert len(res) == 3
        match_res_0 = re.match(dict_diff, res["file.yaml"])
        match_res_1 = re.match(
            dict_diff.replace(
                r"are different:\n", r"are different:\nKwargs used: \{'tolerance': 0\}\n"
            ),
            res["file.json"],
        )
        match_res_2 = re.match(xml_diff, res["file.xml"])

        for match_i in [match_res_0, match_res_1, match_res_2]:
            assert match_i is not None

    def test_unknown_comparator(self, ref_tree, res_tree_diff, registry_reseter):
        dir_content_diff.unregister_comparator(".yaml")
        res = compare_trees(ref_tree, res_tree_diff)
        match = re.match(
            r"The files '\S*/ref/file.yaml' and '\S*/res/file.yaml' are different.",
            res["file.yaml"],
        )
        assert match is not None

    def test_nested_files(self, ref_with_nested_file, res_diff_with_nested_file):
        res = compare_trees(ref_with_nested_file, res_diff_with_nested_file)
        match = re.match(
            r"The files '\S*/ref/level1/level2/level3/file.pdf' and "
            r"'\S*/res/level1/level2/level3/file.pdf' are different\.",
            res["level1/level2/level3/file.pdf"],
        )
        assert match is not None

    def test_fix_dot_notation(self, ref_tree, res_tree_diff, pdf_diff, dict_diff, xml_diff):
        specific_args = {"file.yaml": {"args": [None, None, None, False, 0, True]}}
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert len(res) == 4
        match_res_0 = re.match(pdf_diff, res["file.pdf"])
        match_res_1 = re.match(
            dict_diff.replace(
                r"are different:\n",
                r"are different:\nArgs used: \[None, None, None, False, 0, True\]\n",
            ),
            res["file.yaml"],
        )
        match_res_2 = re.match(dict_diff, res["file.json"])
        match_res_3 = re.match(xml_diff, res["file.xml"])

        for match_i in [match_res_0, match_res_1, match_res_2, match_res_3]:
            assert match_i is not None

    def test_format_inside_diff(self, ref_tree, res_tree_diff, dict_diff):
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
                formatted = [comparator.format(i) for i in diffs]

                return formatted

        res = compare_trees(ref_tree, res_tree_diff, comparators={".json": JsonComparator()})

        match = re.match(dict_diff, res["file.json"])

        assert match is not None


class TestProgrammaticUse:
    """Test specific comparators that could be use programmatically."""

    def test_diff_tree(self, ref_tree, res_tree_diff, pdf_diff, dict_diff):
        res = compare_trees(ref_tree, res_tree_diff, return_raw_diffs=True)

        res_json = res["file.json"]

        assert len(res_json) == 25
        assert len(list(filter(lambda x: x[0] == "change", res_json))) == 17
        assert len(list(filter(lambda x: x[0] == "add", res_json))) == 4
        assert len(list(filter(lambda x: x[0] == "remove", res_json))) == 4
