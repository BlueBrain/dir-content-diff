"""Test the pytest plugin."""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest


@pytest.fixture
def tmp_conftest(ref_tree, res_tree_equal, ref_csv, res_csv_equal):
    """Create a temporary conftest file."""
    return f"""
        from pathlib import Path

        import pytest

        @pytest.fixture
        def ref_path():
            return Path("{ref_tree}")

        @pytest.fixture
        def res_path():
            return Path("{res_tree_equal}")
        """


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
    """Test that the formatted files are properly exported."""
    args = []

    if export_suffix is None:
        suffix = "_FORMATTED"
    else:
        suffix = export_suffix
    expected_dir = f"""res_path.with_name(res_path.name + "{suffix}")"""

    if not do_export:
        tester = f"""assert not {expected_dir}.exists()"""
    else:
        args.append("--dcd-export-formatted-data")
        if export_suffix is not None:
            args.append("--dcd-export-suffix")
            args.append(export_suffix)
        tester = """assert sorted(expected_dir.iterdir()) == [
            (expected_dir / "file").with_suffix(ext)
            for ext in [".csv", ".ini", ".json", ".xml", ".yaml"]
        ]"""

    expected_dir_str = f"""expected_dir = {expected_dir}"""
    remover = """rmtree(expected_dir, ignore_errors=True)"""

    # create a temporary conftest.py file
    pytester.makeconftest(tmp_conftest)

    # create a temporary pytest test file
    pytester.makepyfile(
        f"""
        from shutil import rmtree

        import dir_content_diff
        import dir_content_diff.pandas
        from dir_content_diff import assert_equal_trees

        dir_content_diff.reset_comparators()
        dir_content_diff.pandas.register()


        def test_export_formatted_data_default(ref_path, res_path):
            {expected_dir_str}
            {remover}
            assert_equal_trees(ref_path, res_path)
            {tester}


        def test_export_formatted_data_no_suffix(ref_path, res_path):
            expected_dir = res_path.with_name(res_path.name + "_FORMATTED")
            {remover}

            assert_equal_trees(ref_path, res_path, export_formatted_files={do_export})
            {tester}


        def test_export_formatted_data_suffix(ref_path, res_path):
            expected_dir = res_path.with_name(res_path.name + "{suffix}")
            {remover}

            assert_equal_trees(
                ref_path,
                res_path,
                export_formatted_files="{suffix if do_export else False}",
            )
            {tester}

        """
    )

    # run all tests with pytest
    result = pytester.runpytest(*args)

    # check that all 3 tests passed
    result.assert_outcomes(passed=3)
