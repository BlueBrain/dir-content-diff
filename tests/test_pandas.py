"""Test the Pandas extension of the dir-content-diff package."""
# pylint: disable=missing-function-docstring
# pylint: disable=no-self-use
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import re
from pathlib import Path

import pandas as pd
import pytest

import dir_content_diff
import dir_content_diff.pandas
from dir_content_diff import compare_trees


class TestRegistry:
    """Test the internal registry."""

    def test_pandas_register(self, registry_reseter):
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
        }

        dir_content_diff.pandas.register_pandas()
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".csv": dir_content_diff.pandas.CsvComparator(),
            ".tsv": dir_content_diff.pandas.CsvComparator(),
        }


@pytest.fixture
def pandas_registry_reseter(registry_reseter):
    dir_content_diff.pandas.register_pandas()


@pytest.fixture
def ref_csv(ref_tree):
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
    df = pd.read_csv(ref_csv, index_col="index")
    filename = res_tree_equal / "file.csv"
    df.to_csv(filename, index=True, index_label="index")
    return filename


@pytest.fixture
def res_csv_diff(ref_csv, res_tree_diff):
    df = pd.read_csv(ref_csv, index_col="index")
    df.loc["idx1", "col_a"] *= 10
    df.loc["idx2", "col_b"] += "_new"
    filename = res_tree_diff / "file.csv"
    df.to_csv(filename, index=True, index_label="index")
    return filename


@pytest.fixture
def csv_diff():
    return (
        r"""The files '\S*/file.csv' and '\S*/file.csv' are different:\n\n"""
        r"""Column 'col_a': Series are different\n\n"""
        r"""Series values are different \(33.33333 %\)\n"""
        r"""\[index\]: \[0, 1, 2\]\n"""
        r"""\[left\]:  \[1, 2, 3\]\n"""
        r"""\[right\]: \[10, 2, 3\]\n\n"""
        r"""Column 'col_b': Series are different\n\n"""
        r"""Series values are different \(33.33333 %\)\n"""
        r"""\[index\]: \[0, 1, 2\]\n\[left\]:  \[a, b, c\]\n\[right\]: \[a, b_new, c\]"""
    )


class TestEqualTrees:
    """Tests that should return no difference."""

    def test_diff_tree(
        self, ref_tree, ref_csv, res_tree_equal, res_csv_equal, pandas_registry_reseter
    ):
        res = compare_trees(ref_tree, res_tree_equal)
        assert res == {}

    def test_specific_args(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_diff, pandas_registry_reseter
    ):
        specific_args = {
            "file.csv": {
                "kwargs": {
                    "atol": 100000,
                    "ignore_columns": ["col_b"],
                }
            }
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        # The CSV file is considered as equal thanks to the given kwargs
        assert len(res) == 3
        assert re.match(".*/file.csv.*", str(res)) is None

    def test_replace_pattern(
        self, ref_tree, ref_csv, res_tree_equal, res_csv_equal, pandas_registry_reseter
    ):
        # Add a column with paths in the CSV file
        ref_df = pd.read_csv(ref_csv, index_col="index")
        ref_df["test_path"] = "relative_path/test.file"
        relative_path = "relative_path/test.file"
        absolute_path = str(res_tree_equal / relative_path)
        path_data = (
            f"Some text before the first path: {relative_path} some text after the first path.\n"
            f"Some text before the second path: {relative_path} some text after the second path."
        )
        ref_df["test_data_with_path"] = path_data
        ref_df["test_path_only_in_ref"] = relative_path
        ref_df.to_csv(ref_csv, index=True, index_label="index")

        res_df = pd.read_csv(res_csv_equal, index_col="index")
        res_df["test_path"] = absolute_path
        res_df["test_data_with_path"] = path_data.replace(relative_path, absolute_path, 1)
        res_df["test_path_only_in_res"] = absolute_path
        res_df.to_csv(res_csv_equal, index=True, index_label="index")

        # Check that the missing column is found
        specific_args = {
            "file.csv": {
                "kwargs": {
                    "replace_pattern": {
                        (str(res_tree_equal), ""): [
                            "test_path",
                            "test_data_with_path",
                            "test_path_only_in_ref",
                            "test_path_only_in_res",
                        ]
                    }
                }
            }
        }
        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert len(res) == 1
        res_csv = res["file.csv"]
        match_res = re.match(
            r"The files '\S*/ref/file.csv' and '\S*/res/file.csv' are different:\n"
            r"Kwargs used: {'replace_pattern': {.*}}\n\n"
            r"Column 'test_path_only_in_ref': The column is missing in the compared DataFrame, "
            r"please fix the 'replace_pattern' argument.\n\n"
            r"Column 'test_path_only_in_res': The column is missing in the reference DataFrame, "
            r"please fix the 'replace_pattern' argument.",
            res_csv,
        )
        assert match_res is not None

        # Test with regex flag
        specific_args = {
            "file.csv": {
                "kwargs": {
                    "replace_pattern": {
                        (str(res_tree_equal), "", re.DOTALL): [
                            "test_path",
                            "test_data_with_path",
                            "test_path_only_in_ref",
                            "test_path_only_in_res",
                        ]
                    }
                }
            }
        }
        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert len(res) == 1
        res_csv = res["file.csv"]
        match_res = re.match(
            r"The files '\S*/ref/file.csv' and '\S*/res/file.csv' are different:\n"
            r"Kwargs used: {'replace_pattern': {.*}}\n\n"
            r"Column 'test_path_only_in_ref': The column is missing in the compared DataFrame, "
            r"please fix the 'replace_pattern' argument.\n\n"
            r"Column 'test_path_only_in_res': The column is missing in the reference DataFrame, "
            r"please fix the 'replace_pattern' argument.",
            res_csv,
        )
        assert match_res is not None

        # Test with only nan values in column
        for df_path in [ref_csv, res_csv_equal]:
            df = pd.read_csv(df_path, index_col="index")
            df["test_path"] = None
            df.to_csv(df_path, index=True, index_label="index")

        res = compare_trees(ref_tree, res_tree_equal, specific_args=specific_args)

        assert len(res) == 1
        res_csv = res["file.csv"]
        match_res = re.match(
            r"The files '\S*/ref/file.csv' and '\S*/res/file.csv' are different:\n"
            r"Kwargs used: {'replace_pattern': {.*}}\n\n"
            r"Column 'test_path_only_in_ref': The column is missing in the compared DataFrame, "
            r"please fix the 'replace_pattern' argument.\n\n"
            r"Column 'test_path_only_in_res': The column is missing in the reference DataFrame, "
            r"please fix the 'replace_pattern' argument.",
            res_csv,
        )
        assert match_res is not None

    def test_save_csv_file(self, tmpdir, ref_csv, res_csv_equal, pandas_registry_reseter):
        # Add a column with relative paths in the CSV file
        ref_df = pd.read_csv(ref_csv, index_col="index")
        ref_df["test_path"] = "relative_path/test.file"
        relative_path = "relative_path/test.file"
        absolute_root = Path("/test/absolute/path")
        absolute_path = str(absolute_root / relative_path)
        path_data = (
            f"Some text before the first path: {relative_path} some text after the first path.\n"
            f"Some text before the second path: {relative_path} some text after the second path."
        )
        ref_df["test_data_with_path"] = path_data
        ref_df["test_path_only_in_ref"] = relative_path
        ref_df.to_csv(ref_csv, index=True, index_label="index")

        res_df = pd.read_csv(res_csv_equal, index_col="index")
        res_df["test_path"] = absolute_path
        res_df["test_data_with_path"] = path_data.replace(relative_path, absolute_path, 1)
        res_df["test_path_only_in_res"] = absolute_path
        res_df.to_csv(res_csv_equal, index=True, index_label="index")

        # Check that the missing column is found
        replace_pattern = {
            (str(absolute_root), ""): [
                "test_path",
                "test_data_with_path",
                "test_path_only_in_ref",
                "test_path_only_in_res",
            ]
        }

        res = dir_content_diff.pandas.save_csv_file(
            res_csv_equal,
            str(tmpdir / "res.csv"),
            replace_pattern=replace_pattern,
            read_csv_kwargs={"index_col": "index"},
        )

        assert len(res) == 1
        test_path_only_in_ref_msg = (
            "The column is missing in the compared DataFrame, please fix the 'replace_pattern' "
            "argument."
        )
        assert res["test_path_only_in_ref"] == test_path_only_in_ref_msg

        res_with_ref = dir_content_diff.pandas.save_csv_file(
            res_csv_equal,
            str(tmpdir / "res_with_ref.csv"),
            replace_pattern=replace_pattern,
            ref_path=ref_csv,
        )

        assert len(res_with_ref) == 2
        assert res_with_ref["test_path_only_in_ref"] == test_path_only_in_ref_msg
        assert res_with_ref["test_path_only_in_res"] == (
            "The column is missing in the reference DataFrame, please fix the 'replace_pattern' "
            "argument."
        )


class TestDiffTrees:
    """Tests that should return differences."""

    def test_diff_tree(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_diff, csv_diff, pandas_registry_reseter
    ):
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 4
        res_csv = res["file.csv"]
        match_res = re.match(csv_diff, res_csv)
        assert match_res is not None

    def test_read_csv_kwargs(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_diff, csv_diff, pandas_registry_reseter
    ):
        specific_args = {
            "file.csv": {
                "kwargs": {"load_kwargs": {"header": None, "skiprows": 1, "prefix": "col_"}}
            }
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert len(res) == 4
        res_csv = res["file.csv"]
        match_res = re.match(csv_diff.replace("col_a", "col_1").replace("col_b", "col_2"), res_csv)
        assert match_res is not None

    def test_missing_column(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_equal, csv_diff, pandas_registry_reseter
    ):
        # Rename a column from the CSV file
        df = pd.read_csv(res_csv_equal, index_col="index")
        df.rename(columns={"col_c": "new_col_c"}, inplace=True)
        df.to_csv(res_csv_equal, index=True, index_label="index")

        # Check that the missing column is found
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 1
        res_csv = res["file.csv"]
        match_res = re.match(
            r"The files '\S*/ref/file.csv' and '\S*/res/file.csv' are different:\n\n"
            r"Column 'col_c': The column is missing in the compared DataFrame.\n\n"
            r"Column 'new_col_c': The column is missing in the reference DataFrame.",
            res_csv,
        )
        assert match_res is not None
