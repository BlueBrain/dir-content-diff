"""Test the CLI exit codes of the ``dir-content-diff`` package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2026 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import pytest

import dir_content_diff.cli


class TestCliExitCode:
    """Tests of the CLI exit code, following the ``diff`` convention."""

    @staticmethod
    def _invoke_cli(tmp_path, cli_runner, ref_content, comp_content, compare_files):
        """Create reference and compared inputs and invoke the CLI on them."""
        ref_tree = tmp_path / "ref"
        comp_tree = tmp_path / "comp"
        ref_tree.mkdir()
        comp_tree.mkdir()
        ref_file = ref_tree / "file.txt"
        comp_file = comp_tree / "file.txt"
        ref_file.write_text(ref_content, encoding="utf-8")
        comp_file.write_text(comp_content, encoding="utf-8")

        args = (
            [str(ref_file), str(comp_file)]
            if compare_files
            else [str(ref_tree), str(comp_tree)]
        )
        return cli_runner.invoke(dir_content_diff.cli.main, args)

    @pytest.mark.parametrize(
        "compare_files",
        [
            pytest.param(False, id="trees"),
            pytest.param(True, id="files"),
        ],
    )
    def test_equal_inputs_exit_zero(self, tmp_path, cli_runner, compare_files):
        """Test that the exit code is 0 when no difference is found."""
        result = self._invoke_cli(tmp_path, cli_runner, "same", "same", compare_files)
        assert result.exit_code == 0
        assert result.exception is None

    @pytest.mark.parametrize(
        "compare_files",
        [
            pytest.param(False, id="trees"),
            pytest.param(True, id="files"),
        ],
    )
    def test_different_inputs_exit_one(self, tmp_path, cli_runner, compare_files):
        """Test that the exit code is 1 when differences are found."""
        # NOTE: the contents must have different lengths: the default comparator
        # relies on ``filecmp.cmp`` with ``shallow=True``, so same-size files
        # created within the same mtime tick compare as equal.
        result = self._invoke_cli(
            tmp_path, cli_runner, "hello", "world!", compare_files
        )
        assert result.exit_code == 1
        assert isinstance(result.exception, SystemExit)
        assert result.exception.code == 1
