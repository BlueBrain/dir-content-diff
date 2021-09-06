"""Extension module to process files with Voxcell."""
import numpy as np

try:
    from voxcell import CellCollection
    from voxcell import VoxelData
except ImportError as e:  # pragma: no cover
    raise ImportError("Could not import voxcell package, please install it.") from e

from dir_content_diff import register_comparator
from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.pandas import DataframeComparator


class NrrdComparator(BaseComparator):
    """Comparator for NRRD files."""

    def load(self, path, **kwargs):
        """Load a NRRD file into a :class:`numpy.ndarray`."""
        return VoxelData.load_nrrd(path, **kwargs).raw

    def diff(self, ref, comp, precision=None):
        """Compare data from two NRRD files.

        Note: NRRD files can contain their creation date, so their hashes are depends on
        this creation date, even if the actual data are the same. This comparator only compares the
        actual data in the files.

        Args:
            ref_path (str): The path to the reference CSV file.
            comp_path (str): The path to the compared CSV file.
            precision (int): The desired precision, default is exact precision.

        Returns:
            bool or str: ``False`` if the DataFrames are considered as equal or a string explaining
            why they are not considered as equal.
        """
        try:
            if precision is not None:
                np.testing.assert_array_almost_equal(ref, comp, decimal=precision)
            else:
                np.testing.assert_array_equal(ref, comp)
            return False
        except AssertionError as exception:
            return exception.args

    def format(self, difference):
        """Format one element difference."""
        return difference

    def report(self, ref_file, comp_file, formatted_differences, diff_args, diff_kwargs, **kwargs):
        """Create a report from the formatted differences."""
        if "precision" not in diff_kwargs:
            diff_kwargs["precision"] = None
        return super().report(
            ref_file,
            comp_file,
            formatted_differences,
            diff_args,
            diff_kwargs,
            **kwargs,
        )


class Mvd3Comparator(DataframeComparator):
    """Comparator for MVD3 files.

    Note: MVD3 files can contain their creation date, so their hashes are depends on
    this creation date, even if the data are the same.

    The ``diff`` function of this comparator calls
    :func:`dir_content_diff.pandas.compare_dataframes`, read the doc of this function for details
    on args and kwargs.
    """

    def load(self, path, **kwargs):
        """Load a MVD3 file into a :class:`Pandas.DataFrames`."""
        return CellCollection.load_mvd3(path, **kwargs).as_dataframe()


def register_voxcell():
    """Register Voxcell extensions."""
    register_comparator(".nrrd", NrrdComparator())
    register_comparator(".mvd3", Mvd3Comparator())
