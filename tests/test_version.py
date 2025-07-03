"""Test the version of the ``dir-content-diff`` package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

from importlib.metadata import version

import dir_content_diff


def test_version():
    """Test the version of the dir-content-diff package."""
    pkg_version = version("dir-content-diff")
    assert dir_content_diff.__version__ == pkg_version
