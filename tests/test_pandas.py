"""Test the Pandas extension of the ``dir-content-diff`` package."""
# pylint: disable=missing-function-docstring
# pylint: disable=no-self-use
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=use-implicit-booleaness-not-comparison
import re

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
            ".xml": dir_content_diff.XmlComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
        }

        dir_content_diff.pandas.register()
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".xml": dir_content_diff.XmlComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".csv": dir_content_diff.pandas.CsvComparator(),
            ".tsv": dir_content_diff.pandas.CsvComparator(),
        }


@pytest.fixture
def pandas_registry_reseter(registry_reseter):
    dir_content_diff.pandas.register()


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
                "atol": 100000,
                "ignore_columns": ["col_b"],
            }
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        # The CSV file is considered as equal thanks to the given kwargs
        assert len(res) == 4
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
                "format_data_kwargs": {
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
            r"Kwargs used for formatting data: {'replace_pattern': {.*}}\n\n"
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
                "format_data_kwargs": {
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
            r"Kwargs used for formatting data: {'replace_pattern': {.*}}\n\n"
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
            r"Kwargs used for formatting data: {'replace_pattern': {.*}}\n\n"
            r"Column 'test_path_only_in_ref': The column is missing in the compared DataFrame, "
            r"please fix the 'replace_pattern' argument.\n\n"
            r"Column 'test_path_only_in_res': The column is missing in the reference DataFrame, "
            r"please fix the 'replace_pattern' argument.",
            res_csv,
        )
        assert match_res is not None


class TestDiffTrees:
    """Tests that should return differences."""

    def test_diff_tree(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_diff, csv_diff, pandas_registry_reseter
    ):
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 5
        res_csv = res["file.csv"]
        match_res = re.match(csv_diff, res_csv)
        assert match_res is not None

    def test_read_csv_kwargs(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_diff, csv_diff, pandas_registry_reseter
    ):
        specific_args = {
            "file.csv": {"load_kwargs": {"header": None, "skiprows": 1, "prefix": "col_"}}
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert len(res) == 5
        res_csv = res["file.csv"]
        kwargs_msg = (
            "Kwargs used for loading data: {'header': None, 'skiprows': 1, 'prefix': 'col_'}\n"
        )
        assert kwargs_msg in res_csv
        match_res = re.match(
            csv_diff.replace("col_a", "col_1").replace("col_b", "col_2"),
            res_csv.replace(kwargs_msg, ""),
        )
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
