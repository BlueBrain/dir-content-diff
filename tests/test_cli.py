"""Test the CLI of the ``dir-content-diff`` package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2024 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import json
import logging

import pytest
import yaml

import dir_content_diff
import dir_content_diff.cli


class TestCli:
    @pytest.fixture
    def config(self, tmp_path):
        """The config as a dict."""
        return {"file.pdf": {"tempdir": str(tmp_path)}}

    @pytest.fixture
    def config_json(self, config):
        """The config as a JSON string."""
        return json.dumps(config)

    @pytest.fixture
    def config_yaml(self, config, tmp_path):
        """The config as a YAML file."""
        filepath = tmp_path / "config.yaml"
        with filepath.open("w", encoding="utf-8") as f:
            yaml.dump(config, f)
        return filepath

    @pytest.fixture
    def config_str(self, request):
        """The string given to the CLI to pass the config."""
        return request.getfixturevalue(request.param)

    def test_help(self, cli_runner):
        """Test the --help option."""
        result = cli_runner.invoke(dir_content_diff.cli.main, ["--help"])
        assert "A command line tool for directory or file comparison." in result.stdout

    @pytest.mark.parametrize(
        "config_str", ["config_json", "config_yaml"], indirect=True
    )
    def test_equal_tree(
        self, tmp_path, ref_tree, res_tree_equal, config_str, cli_runner, caplog
    ):
        """Test with equal trees."""
        caplog.set_level(logging.INFO, logger="dir-content-diff")
        result = cli_runner.invoke(
            dir_content_diff.cli.main,
            [str(ref_tree), str(res_tree_equal), "--config", config_str],
        )
        assert result.stdout == ""
        assert caplog.messages == [
            f"No difference found between '{ref_tree}' and '{res_tree_equal}'"
        ]
        assert (tmp_path / "diff-pdf" / "file.pdf" / "diff-1.png").exists()

    @pytest.mark.parametrize(
        "config_str", ["config_json", "config_yaml"], indirect=True
    )
    def test_diff_tree(
        self, tmp_path, ref_tree, res_tree_diff, config_str, cli_runner, caplog
    ):
        """Test with different trees."""
        caplog.set_level(logging.INFO, logger="dir-content-diff")
        result = cli_runner.invoke(
            dir_content_diff.cli.main,
            [str(ref_tree), str(res_tree_diff), "--config", config_str],
        )
        assert result.stdout == ""
        assert len(caplog.messages) == 1
        assert (
            f"Differences found between '{ref_tree}' and '{res_tree_diff}':"
            in caplog.messages[0]
        )
        for i in ref_tree.iterdir():
            ref_file = (ref_tree / "file").with_suffix(i.suffix)
            res_file = (res_tree_diff / "file").with_suffix(i.suffix)
            assert (
                f"The files '{ref_file}' and '{res_file}' are different:"
                in caplog.messages[0]
            )
        assert (tmp_path / "diff-pdf" / "file.pdf" / "diff-1.png").exists()


def test_entry_point(script_runner):
    """Test the entry point."""
    ret = script_runner.run("dir-content-diff", "--version")
    assert ret.success
    assert "dir-content-diff, version " in ret.stdout
    assert ret.stderr == ""
