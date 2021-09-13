"""Test the pytest plugin."""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest


@pytest.fixture
def tmp_conftest(ref_tree, res_tree_equal, ref_csv, res_csv_equal):
    return """
        from pathlib import Path

        import pytest

        @pytest.fixture
        def ref_path():
            return Path("{}")

        @pytest.fixture
        def res_path():
            return Path("{}")
        """.format(
        ref_tree, res_tree_equal
    )


@pytest.mark.parametrize(
    "do_export, export_suffix",
    [
        [False, None],
        [False, "_CMD_SUFFIX"],
        [True, None],
        [True, "_CMD_SUFFIX"],
    ],
)
def test_export_formatted_data(
    ref_tree,
    res_tree_equal,
    ref_csv,
    res_csv_equal,
    tmp_conftest,
    pytester,
    do_export,
    export_suffix,
    registry_reseter,
):
    args = []
    if not do_export:
        expected_dir = """res_path.with_name(res_path.name + "_FORMATTED")"""
        tester = """assert not {}.exists()""".format(expected_dir)
    else:
        if export_suffix is None:
            suffix = "_FORMATTED"
        else:
            suffix = export_suffix

        expected_dir = """res_path.with_name(res_path.name + "{suffix}")""".format(suffix=suffix)
        args.append("--dcd-export-formatted-data")
        if export_suffix is not None:
            args.append("--dcd-export-suffix")
            args.append(export_suffix)
        tester = """assert list(expected_dir.iterdir()) == [expected_dir / "file.csv"]"""

    expected_dir_str = """expected_dir = {expected_dir}""".format(expected_dir=expected_dir)
    remover = """rmtree(expected_dir, ignore_errors=True)"""

    # create a temporary conftest.py file
    pytester.makeconftest(tmp_conftest)

    # create a temporary pytest test file
    pytester.makepyfile(
        """
        from shutil import rmtree

        import dir_content_diff
        import dir_content_diff.pandas
        from dir_content_diff import assert_equal_trees

        dir_content_diff.reset_comparators()
        dir_content_diff.pandas.register_pandas()


        def test_export_formatted_data_default(ref_path, res_path):
            {expected_dir_str}
            {remover}
            assert_equal_trees(ref_path, res_path)
            {tester}


        def test_export_formatted_data_no_suffix(ref_path, res_path):
            expected_dir = res_path.with_name(res_path.name + "_FORMATTED")
            rmtree(expected_dir, ignore_errors=True)

            assert_equal_trees(ref_path, res_path, export_formatted_files=True)
            assert list(expected_dir.iterdir()) == [expected_dir / "file.csv"]


        def test_export_formatted_data_suffix(ref_path, res_path):
            expected_dir = res_path.with_name(res_path.name + "_NEW_SUFFIX")
            rmtree(expected_dir, ignore_errors=True)

            assert_equal_trees(ref_path, res_path, export_formatted_files="_NEW_SUFFIX")
            assert list(expected_dir.iterdir()) == [expected_dir / "file.csv"]

        """.format(
            expected_dir_str=expected_dir_str,
            remover=remover,
            tester=tester,
        )
    )

    # run all tests with pytest
    result = pytester.runpytest(*args)

    # check that all 3 tests passed
    result.assert_outcomes(passed=3)
