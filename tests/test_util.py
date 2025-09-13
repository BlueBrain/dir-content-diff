"""Test the ``dir-content-diff.util`` package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import pytest

import dir_content_diff.util


def test_import_error_message(monkeypatch, caplog):
    """Test missing dependencies."""
    caplog.clear()
    dir_content_diff.util.import_error_message("pandas")
    assert caplog.messages == [
        "Loading the pandas module without the required dependencies installed "
        "(requirements are the following: pandas>=1.4, pyarrow>=11 and tables>=3.7). "
        "Will crash at runtime if the related functionalities are used. "
        "These dependencies can be installed with 'pip install dir-content-diff[pandas]'."
    ]

    with pytest.raises(
        KeyError,
        match=(
            "The module UNKNOWN_MODULE has no registered dependency, please add dependencies to "
            "the dependencies.json file"
        ),
    ):
        dir_content_diff.util.import_error_message("UNKNOWN_MODULE")

    monkeypatch.setitem(
        dir_content_diff.util.COMPARATOR_DEPENDENCIES,
        "TEST_MODULE",
        ["DUMMY-DEPENDENCY"],
    )
    caplog.clear()
    dir_content_diff.util.import_error_message("TEST_MODULE")
    assert caplog.messages == [
        "Loading the TEST_MODULE module without the required dependencies installed "
        "(requirement is the following: DUMMY-DEPENDENCY). "
        "Will crash at runtime if the related functionalities are used. "
        "These dependencies can be installed with 'pip install dir-content-diff[TEST_MODULE]'."
    ]
