"""Test the Pandas extension of the ``dir-content-diff`` package."""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=use-implicit-booleaness-not-comparison
import re
import sys

import pandas as pd
import pytest

import dir_content_diff
import dir_content_diff.pandas
from dir_content_diff import assert_equal_trees
from dir_content_diff import compare_trees


class TestRegistry:
    """Test the internal registry."""

    def test_pandas_register(self, registry_reseter):
        """Test registering the pandas plugin."""
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".cfg": dir_content_diff.IniComparator(),
            ".conf": dir_content_diff.IniComparator(),
            ".ini": dir_content_diff.IniComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".xml": dir_content_diff.XmlComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
        }

        dir_content_diff.pandas.register()
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".cfg": dir_content_diff.IniComparator(),
            ".conf": dir_content_diff.IniComparator(),
            ".ini": dir_content_diff.IniComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".xml": dir_content_diff.XmlComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".csv": dir_content_diff.pandas.CsvComparator(),
            ".tsv": dir_content_diff.pandas.CsvComparator(),
            ".h4": dir_content_diff.pandas.HdfComparator(),
            ".h5": dir_content_diff.pandas.HdfComparator(),
            ".hdf": dir_content_diff.pandas.HdfComparator(),
            ".hdf4": dir_content_diff.pandas.HdfComparator(),
            ".hdf5": dir_content_diff.pandas.HdfComparator(),
            ".feather": dir_content_diff.pandas.FeatherComparator(),
            ".parquet": dir_content_diff.pandas.ParquetComparator(),
            ".dta": dir_content_diff.pandas.StataComparator(),
        }


@pytest.fixture
def pandas_registry_reseter(registry_reseter):
    """Register the pandas plugin and then reset the registry after the test."""
    dir_content_diff.pandas.register()


@pytest.fixture
def ref_data(empty_ref_tree):
    ref_data = {
        "col_a": [1, 2, 3],
        "col_b": ["a", "b", "c"],
        "col_c": [4, 5, 6],
    }
    df = pd.DataFrame(ref_data, index=["idx1", "idx2", "idx3"])
    return df


@pytest.fixture
def ref_hdf5(ref_data, empty_ref_tree):
    """The reference HDF5 file."""
    filename = empty_ref_tree / "file.h5"
    ref_data.to_hdf(filename, key="data", index=True)
    return filename


@pytest.fixture
def ref_feather(ref_data, empty_ref_tree):
    """The reference Feather file."""
    filename = empty_ref_tree / "file.feather"
    ref_data.to_feather(filename)
    return filename


@pytest.fixture
def ref_parquet(ref_data, empty_ref_tree):
    """The reference Parquet file."""
    filename = empty_ref_tree / "file.parquet"
    ref_data.to_parquet(filename)
    return filename


@pytest.fixture
def ref_stata(ref_data, empty_ref_tree):
    """The reference Stata file."""
    filename = empty_ref_tree / "file.dta"
    ref_data.to_stata(filename)
    return filename


def _update_df(df):
    df.loc["idx1", "col_a"] *= 10
    df.loc["idx2", "col_b"] += "_new"


@pytest.fixture
def res_diff_checker():
    """The regex used to check the diff result."""
    return (
        r"The files '\S*/ref/file\.\S*' and '\S*/res/file\.\S*' are different:\n\n"
        r"Column 'col_a': Series are different\n\n"
        r"Series values are different \(33\.33333 %\)\n"
        r"\[index\]: \[idx1, idx2, idx3\]\n"
        r"\[left\]:  \[1, 2, 3\]\n\[right\]: \[10, 2, 3\]\n"
        r"""(At positional index 0, first diff: 1 != 10\n)?\n"""
        r"Column 'col_b': Series are different\n\n"
        r"Series values are different \(33\.33333 %\)\n"
        r"\[index\]: \[idx1, idx2, idx3\]\n"
        r"\[left\]:  \[a, b, c\]\n\[right\]: \[a, b_new, c\]"
        r"""(\nAt positional index 1, first diff: b != b_new)?"""
    )


@pytest.fixture
def res_hdf5_equal(ref_hdf5, empty_res_tree):
    """The result hdf5 file equal to the reference."""
    df = pd.read_hdf(ref_hdf5, index_col="index")
    filename = empty_res_tree / "file.h5"
    df.to_hdf(filename, key="data", index=True)
    return filename


@pytest.fixture
def res_hdf5_diff(ref_hdf5, empty_res_tree):
    """The result hdf5 file different from the reference."""
    df = pd.read_hdf(ref_hdf5, index_col="index")
    _update_df(df)
    filename = empty_res_tree / "file.h5"
    df.to_hdf(filename, key="data", index=True)
    return filename


@pytest.fixture
def res_feather_equal(ref_feather, empty_res_tree):
    """The result feather file equal to the reference."""
    df = pd.read_feather(ref_feather)
    filename = empty_res_tree / "file.feather"
    df.to_feather(filename)
    return filename


@pytest.fixture
def res_feather_diff(ref_feather, empty_res_tree):
    """The result feather file different from the reference."""
    df = pd.read_feather(ref_feather)
    _update_df(df)
    filename = empty_res_tree / "file.feather"
    df.to_feather(filename)
    return filename


@pytest.fixture
def res_parquet_equal(ref_parquet, empty_res_tree):
    """The result parquet file equal to the reference."""
    df = pd.read_parquet(ref_parquet)
    filename = empty_res_tree / "file.parquet"
    df.to_parquet(filename)
    return filename


@pytest.fixture
def res_parquet_diff(ref_parquet, empty_res_tree):
    """The result parquet file different from the reference."""
    df = pd.read_parquet(ref_parquet)
    _update_df(df)
    filename = empty_res_tree / "file.parquet"
    df.to_parquet(filename)
    return filename


@pytest.fixture
def res_stata_equal(ref_stata, empty_res_tree):
    """The result stata file equal to the reference."""
    df = pd.read_stata(ref_stata, index_col="index")
    filename = empty_res_tree / "file.dta"
    df.to_stata(filename)
    return filename


@pytest.fixture
def res_stata_diff(ref_stata, empty_res_tree):
    """The result stata file different from the reference."""
    df = pd.read_stata(ref_stata, index_col="index")
    _update_df(df)
    filename = empty_res_tree / "file.dta"
    df.to_stata(filename)
    return filename


class TestEqualTrees:
    """Tests that should return no difference."""

    def test_diff_tree(
        self, ref_tree, ref_csv, res_tree_equal, res_csv_equal, pandas_registry_reseter
    ):
        """Test that no difference is returned."""
        res = compare_trees(ref_tree, res_tree_equal)
        assert res == {}

    def test_specific_args(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_diff, pandas_registry_reseter
    ):
        """Test specific args."""
        specific_args = {
            "file.csv": {
                "atol": 100000,
                "ignore_columns": ["col_b"],
            }
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        # The CSV file is considered as equal thanks to the given kwargs
        assert len(res) == 5
        assert re.match(".*/file.csv.*", str(res)) is None

    def test_replace_pattern(
        self, ref_tree, ref_csv, res_tree_equal, res_csv_equal, pandas_registry_reseter
    ):
        """Test the feature to replace a given pattern in files."""
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
            r"The files '\S*/ref/file\.csv' and '\S*/res/file\.csv' are different:\n"
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
            r"The files '\S*/ref/file\.csv' and '\S*/res/file\.csv' are different:\n"
            r"Kwargs used for formatting data: {'replace_pattern': {.*}}\n\n"
            r"Column 'test_path_only_in_ref': The column is missing in the compared DataFrame, "
            r"please fix the 'replace_pattern' argument\.\n\n"
            r"Column 'test_path_only_in_res': The column is missing in the reference DataFrame, "
            r"please fix the 'replace_pattern' argument\.",
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
            r"The files '\S*/ref/file\.csv' and '\S*/res/file\.csv' are different:\n"
            r"Kwargs used for formatting data: {'replace_pattern': {.*}}\n\n"
            r"Column 'test_path_only_in_ref': The column is missing in the compared DataFrame, "
            r"please fix the 'replace_pattern' argument\.\n\n"
            r"Column 'test_path_only_in_res': The column is missing in the reference DataFrame, "
            r"please fix the 'replace_pattern' argument\.",
            res_csv,
        )
        assert match_res is not None

    def _check_equal(self, empty_ref_tree, empty_res_tree):
        assert_equal_trees(empty_ref_tree, empty_res_tree, export_formatted_files=True)
        ref_files = list(empty_ref_tree.rglob("*"))
        res_files = list(empty_res_tree.rglob("*"))
        assert len(ref_files) == len(res_files)
        return ref_files, res_files

    def test_hdf5_comparator(
        self, empty_ref_tree, empty_res_tree, res_hdf5_equal, pandas_registry_reseter
    ):
        """Test the comparator for HDF5 files."""
        ref_files, res_files = self._check_equal(empty_ref_tree, empty_res_tree)
        for i, j in zip(ref_files, res_files):
            assert pd.read_hdf(i).equals(pd.read_hdf(j))

    @pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
    def test_feather_comparator(
        self, empty_ref_tree, empty_res_tree, res_feather_equal, pandas_registry_reseter
    ):
        """Test the comparator for Feather files."""
        ref_files, res_files = self._check_equal(empty_ref_tree, empty_res_tree)
        for i, j in zip(ref_files, res_files):
            assert pd.read_feather(i).equals(pd.read_feather(j))

    def test_parquet_comparator(
        self, empty_ref_tree, empty_res_tree, res_parquet_equal, pandas_registry_reseter
    ):
        """Test the comparator for Parquet files."""
        ref_files, res_files = self._check_equal(empty_ref_tree, empty_res_tree)
        for i, j in zip(ref_files, res_files):
            assert pd.read_parquet(i).equals(pd.read_parquet(j))

    def test_stata_comparator(
        self, empty_ref_tree, empty_res_tree, res_stata_equal, pandas_registry_reseter
    ):
        """Test the comparator for Stata files."""
        ref_files, res_files = self._check_equal(empty_ref_tree, empty_res_tree)
        for i, j in zip(ref_files, res_files):
            assert pd.read_stata(i).equals(pd.read_stata(j))


class TestDiffTrees:
    """Tests that should return differences."""

    def test_diff_tree(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_diff, csv_diff, pandas_registry_reseter
    ):
        """Test that the returned differences are correct."""
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 6
        res_csv = res["file.csv"]
        match_res = re.match(csv_diff, res_csv)
        assert match_res is not None

    def test_read_csv_kwargs(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_diff, csv_diff, pandas_registry_reseter
    ):
        """Test specific args for the CSV reader."""
        specific_args = {"file.csv": {"load_kwargs": {"header": None, "skiprows": 1}}}
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert len(res) == 6
        res_csv = res["file.csv"]
        kwargs_msg = "Kwargs used for loading data: {'header': None, 'skiprows': 1}\n"
        assert kwargs_msg in res_csv
        match_res = re.match(
            csv_diff.replace("col_a", "1").replace("col_b", "2"),
            res_csv.replace(kwargs_msg, ""),
        )
        assert match_res is not None

    def test_missing_column(
        self, ref_tree, ref_csv, res_tree_diff, res_csv_equal, csv_diff, pandas_registry_reseter
    ):
        """Test the behavior with missing columns in CSV files."""
        # Rename a column from the CSV file
        df = pd.read_csv(res_csv_equal, index_col="index")
        df.rename(columns={"col_c": "new_col_c"}, inplace=True)
        df.to_csv(res_csv_equal, index=True, index_label="index")

        # Check that the missing column is found
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 1
        res_csv = res["file.csv"]
        match_res = re.match(
            r"The files '\S*/ref/file\.csv' and '\S*/res/file\.csv' are different:\n\n"
            r"Column 'col_c': The column is missing in the compared DataFrame.\n\n"
            r"Column 'new_col_c': The column is missing in the reference DataFrame.",
            res_csv,
        )
        assert match_res is not None

    def _check_diff_comparator(
        self, empty_ref_tree, empty_res_tree, res_diff_checker, ext, specific_args=None
    ):
        res = compare_trees(empty_ref_tree, empty_res_tree, specific_args=specific_args)

        assert len(res) == 1
        filename = f"file.{ext}"
        res_ext = res[filename]
        if specific_args is not None and filename in specific_args:
            res_diff_checker = res_diff_checker.replace(
                "' are different:",
                "' are different:\nKwargs used for loading data: "
                f"{specific_args[filename]['load_kwargs']}",
            )
        match_res = re.match(
            res_diff_checker,
            res_ext,
        )
        assert match_res is not None

    def test_hdf5_comparator(
        self,
        empty_ref_tree,
        empty_res_tree,
        res_hdf5_diff,
        res_diff_checker,
        pandas_registry_reseter,
    ):
        """Test the comparator for HDF5 files."""
        self._check_diff_comparator(empty_ref_tree, empty_res_tree, res_diff_checker, "h5")

    @pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
    def test_feather_comparator(
        self,
        empty_ref_tree,
        empty_res_tree,
        res_feather_diff,
        res_diff_checker,
        pandas_registry_reseter,
    ):
        """Test the comparator for feather files."""
        self._check_diff_comparator(empty_ref_tree, empty_res_tree, res_diff_checker, "feather")

    def test_parquet_comparator(
        self,
        empty_ref_tree,
        empty_res_tree,
        res_parquet_diff,
        res_diff_checker,
        pandas_registry_reseter,
    ):
        """Test the comparator for parquet files."""
        self._check_diff_comparator(empty_ref_tree, empty_res_tree, res_diff_checker, "parquet")

    def test_stata_comparator(
        self,
        empty_ref_tree,
        empty_res_tree,
        res_stata_diff,
        res_diff_checker,
        pandas_registry_reseter,
    ):
        """Test the comparator for stata files."""
        specific_args = {"file.dta": {"load_kwargs": {"index_col": "index"}}}
        self._check_diff_comparator(
            empty_ref_tree, empty_res_tree, res_diff_checker, "dta", specific_args=specific_args
        )
