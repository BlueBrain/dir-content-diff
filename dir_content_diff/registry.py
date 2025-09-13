"""Comparator registry management.

This module handles the registration and management of file comparators.
"""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import copy
from collections.abc import Callable
from typing import Union

from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.base_comparators import DefaultComparator
from dir_content_diff.base_comparators import IniComparator
from dir_content_diff.base_comparators import JsonComparator
from dir_content_diff.base_comparators import PdfComparator
from dir_content_diff.base_comparators import XmlComparator
from dir_content_diff.base_comparators import YamlComparator
from dir_content_diff.util import format_ext

# Type alias for comparators
ComparatorType = Union[BaseComparator, Callable]

_DEFAULT_COMPARATORS = {
    None: DefaultComparator(),
    ".cfg": IniComparator(),  # luigi config files
    ".conf": IniComparator(),  # logging config files
    ".ini": IniComparator(),
    ".json": JsonComparator(),
    ".pdf": PdfComparator(),
    ".yaml": YamlComparator(),
    ".yml": YamlComparator(),
    ".xml": XmlComparator(),
}

_COMPARATORS = {}


def reset_comparators():
    """Reset the comparator registry to the default values."""
    _COMPARATORS.clear()
    _COMPARATORS.update(copy.deepcopy(_DEFAULT_COMPARATORS))


# Initialize comparators on module load
reset_comparators()


def get_comparators():
    """Return a copy of the comparator registry."""
    return copy.deepcopy(_COMPARATORS)


def register_comparator(
    ext: str, comparator: ComparatorType, force: bool = False
) -> None:
    """Add a comparator to the registry.

    Args:
        ext: The extension to register.
        comparator: The comparator that should be associated with the given extension.
        force: If set to ``True``, no exception is raised if the given ``ext`` is already
            registered and the comparator is replaced.

    .. note::
        It is possible to create and register custom comparators. The easiest way to do it is to
        derive a class from :class:`dir_content_diff.BaseComparator`.

        Otherwise, the given comparator should be a callable with the following signature:

        .. code-block:: python

            comparator(
                ref_file: str,
                comp_file: str,
                *diff_args: Sequence[Any],
                return_raw_diffs: bool=False,
                **diff_kwargs: Mapping[str, Any],
            ) -> Union[False, str]

        The return type can be Any when used with `return_raw_diffs == True`, else it should be a
        string object.
    """
    ext = format_ext(ext)
    if not force and ext in _COMPARATORS:
        raise ValueError(
            f"The '{ext}' extension is already registered and must be unregistered before being "
            "replaced."
        )
    _COMPARATORS[ext] = comparator


def unregister_comparator(ext: str, quiet: bool = False):
    """Remove a comparator from the registry.

    Args:
        ext: The extension to unregister.
        quiet: If set to ``True``, no exception is raised if the given ``ext`` is not
            registered.

    Returns:
        The removed comparator.
    """
    ext = format_ext(ext)
    if not quiet and ext not in _COMPARATORS:
        raise ValueError(f"The '{ext}' extension is not registered.")
    return _COMPARATORS.pop(ext, None)
