"""Setup for the dir-content-diff package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import json
from pathlib import Path

from setuptools import setup

doc_reqs = [
    "myst_parser",
    "sphinx",
    "sphinx-bluebrain-theme",
]

# Requirements for custom comparators
with (
    Path(__file__).parent / "dir_content_diff" / "comparators" / "dependencies.json"
).open() as f:
    all_comparators = json.load(f)

# Requirements for tests
test_reqs = [
    "dicttoxml>=1.7.16",
    "matplotlib>=3.4",
    "rst2pdf>=0.99",
    "pandas>=1.4",
    "pytest>=6.2",
    "pytest-click>=1.1",
    "pytest-console-scripts>=1.4",
    "pytest-cov>=4.1",
    "pytest-html>=3.2",
]

setup(
    extras_require={
        "all_comparators": list(all_comparators.values()),
        "docs": doc_reqs,
        "test": test_reqs,
        **all_comparators,
    },
)
