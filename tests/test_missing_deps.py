"""Test comparators with missing deps."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2026 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import importlib
import sys
from subprocess import run

import pytest


@pytest.mark.comparators_missing_deps
def test_missing_deps(tmp_path):
    """Test missing dependencies."""
    root_dir = importlib.resources.files("dir_content_diff")  # pylint: disable=no-member
    comparator_dir = root_dir / "comparators"
    imported_comparators = [
        f"import dir_content_diff.comparators.{path.stem}\n"
        for path in sorted(comparator_dir.glob("*.py"))
    ]
    missing_deps_file = tmp_path / "test_missing_deps.py"
    with missing_deps_file.open(mode="w", encoding="utf8") as f:
        f.writelines(imported_comparators)
        f.flush()
    res = run([sys.executable, str(missing_deps_file)], capture_output=True, check=True)
    assert res.stderr.decode() == (
        "Loading the morphio module without the required dependencies installed "
        "(requirements are the following: morphio>=3.3.6 and morph_tool>=2.9). "
        "Will crash at runtime if the related functionalities are used. "
        "These dependencies can be installed with 'pip install dir-content-diff[morphio]'."
        "\n"
        "Loading the voxcell module without the required dependencies installed "
        "(requirements are the following: voxcell>=3.1.1, pynrrd<1.1,>=0.4 and "
        "nptyping>=2.5). "
        "Will crash at runtime if the related functionalities are used. "
        "These dependencies can be installed with 'pip install dir-content-diff[voxcell]'.\n"
    )
