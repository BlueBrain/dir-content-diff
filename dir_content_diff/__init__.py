"""dir-content-diff package.

Simple tool to compare directory contents.
"""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import importlib.metadata

# Import base comparators for backward compatibility
from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.base_comparators import DefaultComparator

# from dir_content_diff.core import _DEFAULT_EXPORT_SUFFIX
# from dir_content_diff.core import _check_config
# from dir_content_diff.core import _split_into_chunks
# Import core comparison functionality
from dir_content_diff.config import ComparisonConfig
from dir_content_diff.core import ComparatorType
from dir_content_diff.core import assert_equal_trees
from dir_content_diff.core import compare_files
from dir_content_diff.core import compare_trees
from dir_content_diff.core import export_formatted_file
from dir_content_diff.core import pick_comparator

# Import comparator registry functionality
# from dir_content_diff.registry import _COMPARATORS
from dir_content_diff.registry import get_comparators
from dir_content_diff.registry import register_comparator
from dir_content_diff.registry import reset_comparators
from dir_content_diff.registry import unregister_comparator

# from dir_content_diff.base_comparators import IniComparator
# from dir_content_diff.base_comparators import JsonComparator
# from dir_content_diff.base_comparators import PdfComparator
# from dir_content_diff.base_comparators import XmlComparator
# from dir_content_diff.base_comparators import YamlComparator

__version__ = importlib.metadata.version("dir-content-diff")

# For backward compatibility, ensure all public functions are available
__all__ = [
    "ComparisonConfig",
    "ComparatorType",
    "assert_equal_trees",
    "compare_files",
    "compare_trees",
    "export_formatted_file",
    "pick_comparator",
    "get_comparators",
    "register_comparator",
    "reset_comparators",
    "unregister_comparator",
    "BaseComparator",
    "DefaultComparator",
    # "IniComparator",
    # "JsonComparator",
    # "PdfComparator",
    # "XmlComparator",
    # "YamlComparator",
    # "_DEFAULT_EXPORT_SUFFIX",
    # "_split_into_chunks",
    # "_check_config",
    # "_COMPARATORS",
]
