"""Test the base features of the dir-content-diff package."""
# pylint: disable=missing-function-docstring
# pylint: disable=no-self-use
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import re

import pytest

import dir_content_diff
from dir_content_diff import assert_equal_trees
from dir_content_diff import compare_trees


class TestRegistry:
    """Test the internal registry."""

    def test_init_register(self, registry_reseter):
        """Test the initial registry with the get_comparators() function."""
        assert dir_content_diff.get_comparators() == {
            ".json": dir_content_diff.compare_json_files,
            ".pdf": dir_content_diff.compare_pdf_files,
            ".yaml": dir_content_diff.compare_yaml_files,
            ".yml": dir_content_diff.compare_yaml_files,
        }

    def test_update_register(self, registry_reseter):
        """Test the functions to update the registry."""
        dir_content_diff.register_comparator(".test_ext", dir_content_diff.compare_json_files)
        assert dir_content_diff.get_comparators() == {
            ".test_ext": dir_content_diff.compare_json_files,
            ".json": dir_content_diff.compare_json_files,
            ".pdf": dir_content_diff.compare_pdf_files,
            ".yaml": dir_content_diff.compare_yaml_files,
            ".yml": dir_content_diff.compare_yaml_files,
        }

        dir_content_diff.unregister_comparator(".yaml")
        dir_content_diff.unregister_comparator("json")  # Test suffix without dot
        assert dir_content_diff.get_comparators() == {
            ".test_ext": dir_content_diff.compare_json_files,
            ".pdf": dir_content_diff.compare_pdf_files,
            ".yml": dir_content_diff.compare_yaml_files,
        }

        dir_content_diff.reset_comparators()
        assert dir_content_diff.get_comparators() == {
            ".json": dir_content_diff.compare_json_files,
            ".pdf": dir_content_diff.compare_pdf_files,
            ".yaml": dir_content_diff.compare_yaml_files,
            ".yml": dir_content_diff.compare_yaml_files,
        }

        with pytest.raises(
            ValueError,
            match=(
                "The '.pdf' extension is already registered and must be unregistered before being "
                "replaced."
            ),
        ):
            dir_content_diff.register_comparator(".pdf", dir_content_diff.compare_json_files)

        with pytest.raises(ValueError, match=("The '.unknown_ext' extension is not registered.")):
            dir_content_diff.unregister_comparator(".unknown_ext")

        dir_content_diff.unregister_comparator(".unknown_ext", quiet=True)
        dir_content_diff.register_comparator(".new_ext", dir_content_diff.compare_json_files)
        assert dir_content_diff.get_comparators() == {
            ".json": dir_content_diff.compare_json_files,
            ".pdf": dir_content_diff.compare_pdf_files,
            ".yaml": dir_content_diff.compare_yaml_files,
            ".yml": dir_content_diff.compare_yaml_files,
            ".new_ext": dir_content_diff.compare_json_files,
        }
        dir_content_diff.register_comparator(
            ".new_ext", dir_content_diff.compare_pdf_files, force=True
        )
        assert dir_content_diff.get_comparators() == {
            ".json": dir_content_diff.compare_json_files,
            ".pdf": dir_content_diff.compare_pdf_files,
            ".yaml": dir_content_diff.compare_yaml_files,
            ".yml": dir_content_diff.compare_yaml_files,
            ".new_ext": dir_content_diff.compare_pdf_files,
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

    def test_diff_tree(self, ref_tree, res_tree_diff, pdf_diff, dict_diff):
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 3
        match_res_0 = re.match(pdf_diff, res["file.pdf"])
        match_res_1 = re.match(dict_diff, res["file.json"])
        match_res_2 = re.match(dict_diff, res["file.yaml"])

        for match_i in [match_res_0, match_res_1, match_res_2]:
            assert match_i is not None

    def test_assert_equal_trees(self, ref_tree, res_tree_diff, pdf_diff, dict_diff):
        pattern = (r"\n\n\n").join([dict_diff, pdf_diff, dict_diff])
        with pytest.raises(AssertionError, match=pattern):
            assert_equal_trees(ref_tree, res_tree_diff)

    def test_diff_ref_empty_res_not_empty(self, empty_ref_tree, res_tree_equal):
        res = compare_trees(empty_ref_tree, res_tree_equal)
        assert res == {}

    def test_diff_ref_not_empty_res_empty(self, ref_tree, empty_res_tree):
        res = compare_trees(ref_tree, empty_res_tree)

        assert len(res) == 3
        match_res_0 = re.match(
            r"The file 'file.pdf' does not exist in '\S*/res'\.", res["file.pdf"]
        )
        match_res_1 = re.match(
            r"The file 'file.yaml' does not exist in '\S*/res'\.", res["file.yaml"]
        )
        match_res_2 = re.match(
            r"The file 'file.json' does not exist in '\S*/res'\.", res["file.json"]
        )

        for match_i in [match_res_0, match_res_1, match_res_2]:
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
            r"Bad\ncomparator",
            res["file.yaml"],
        )
        assert match is not None

    def test_specific_args(self, ref_tree, res_tree_diff, dict_diff):
        specific_args = {
            "file.pdf": {"kwargs": {"threshold": 50}},
            "file.json": {"kwargs": {"tolerance": 0}},
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        # This time the PDF files are considered as equal
        assert len(res) == 2
        match_res_0 = re.match(dict_diff, res["file.yaml"])
        match_res_1 = re.match(
            dict_diff.replace(
                r"are different:\n", r"are different:\nKwargs used: \{'tolerance': 0\}\n"
            ),
            res["file.json"],
        )

        for match_i in [match_res_0, match_res_1]:
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

    def test_fix_dot_notation(self, ref_tree, res_tree_diff, pdf_diff, dict_diff):
        specific_args = {"file.yaml": {"args": [None, None, None, False, 0, True]}}
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert len(res) == 3
        match_res_0 = re.match(pdf_diff, res["file.pdf"])
        match_res_1 = re.match(
            dict_diff.replace(
                r"are different:\n",
                r"are different:\nArgs used: \[None, None, None, False, 0, True\]\n",
            ),
            res["file.yaml"],
        )
        match_res_2 = re.match(dict_diff, res["file.json"])

        for match_i in [match_res_0, match_res_1, match_res_2]:
            assert match_i is not None
