"""Extension module to process morphology files with MorphIO and morph-tool."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

from dir_content_diff import register_comparator
from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.util import import_error_message

try:
    from morph_tool import diff
    from morphio.mut import Morphology
except ImportError:  # pragma: no cover
    import_error_message(__name__)


class MorphologyComparator(BaseComparator):
    """Comparator for morphology files."""

    def load(self, path, **kwargs):
        """Load a morphology file into a :class:`morphio.Morphology` object."""
        return Morphology(path, **kwargs)

    def diff(self, ref, comp, *args, **kwargs):
        """Compare data from two morphology files.

        Args:
            ref_path (str): The path to the reference morphology file.
            comp_path (str): The path to the compared morphology file.
            *args: See :func:`morph_tool.diff` for details.
            **kwargs: See :func:`morph_tool.diff` for details.

        Returns:
            bool or list(str): ``False`` if the morphologies are considered as equal or a list of
            strings explaining why they are not considered as equal.
        """
        diffs = diff(ref, comp, *args, **kwargs)
        if not diffs:
            return False
        return [diffs.info]


def register(force=False):
    """Register morphology file extensions."""
    register_comparator(".asc", MorphologyComparator(), force=force)
    register_comparator(".h5", MorphologyComparator(), force=force)
    register_comparator(".swc", MorphologyComparator(), force=force)
