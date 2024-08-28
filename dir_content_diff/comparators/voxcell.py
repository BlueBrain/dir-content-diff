"""Extension module to process files with Voxcell."""
from dir_content_diff import register_comparator
from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.comparators.pandas import DataframeComparator
from dir_content_diff.util import import_error_message

try:
    import numpy as np
    from voxcell import CellCollection
    from voxcell import VoxelData
except ImportError:  # pragma: no cover
    import_error_message(__name__)


class NrrdComparator(BaseComparator):
    """Comparator for NRRD files."""

    def load(self, path, **kwargs):
        """Load a NRRD file into a :class:`numpy.ndarray`."""
        return VoxelData.load_nrrd(str(path), **kwargs)

    def save(self, data, path, **kwargs):
        """Save data to a NRRD file."""
        return data.save_nrrd(str(path), **kwargs)

    def format_diff(self, difference, **kwargs):
        """Format one element difference."""
        k, v = difference
        return f"\n{k}: {v}"

    def sort(self, differences, **kwargs):
        """Do not sort the entries to keep voxel dimensions as first entry."""
        return differences

    def diff(self, ref, comp, *args, precision=None, **kwargs):
        """Compare data from two NRRD files.

        Note: NRRD files can contain their creation date, so their hashes are depends on
        this creation date, even if the actual data are the same. This comparator only compares the
        actual data in the files.

        Args:
            ref_path (str): The path to the reference CSV file.
            comp_path (str): The path to the compared CSV file.
            precision (int): The desired precision, default is exact precision.

        Returns:
            bool or list(str): ``False`` if the DataFrames are considered as equal or a list of
            strings explaining why they are not considered as equal.
        """
        errors = {}

        try:
            if precision is not None:
                np.testing.assert_array_almost_equal(
                    ref.voxel_dimensions, comp.voxel_dimensions, *args, decimal=precision, **kwargs
                )
            else:
                np.testing.assert_array_equal(
                    ref.voxel_dimensions, comp.voxel_dimensions, *args, **kwargs
                )
        except AssertionError as exception:
            errors["Voxel dimensions"] = exception.args[0]

        try:
            if precision is not None:
                np.testing.assert_array_almost_equal(
                    ref.raw, comp.raw, *args, decimal=precision, **kwargs
                )
            else:
                np.testing.assert_array_equal(ref.raw, comp.raw, *args, **kwargs)
        except AssertionError as exception:
            errors["Internal raw data"] = exception.args[0]

        if len(errors) == 0:
            return False
        return errors

    def report(self, ref_file, comp_file, formatted_differences, diff_args, diff_kwargs, **kwargs):
        """Create a report from the formatted differences."""
        # pylint: disable=arguments-differ
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

    This comparator inherits from the :class:`dir_content_diff.pandas.DataframeComparator`, read
    the doc of this comparator for details on args and kwargs.
    """

    def load(self, path, **kwargs):
        """Load a MVD3 file into a :class:`pandas.DataFrame`."""
        return CellCollection.load_mvd3(path, **kwargs).as_dataframe()

    def save(self, data, path, **kwargs):
        """Save data to a CellCollection file."""
        return CellCollection.from_dataframe(data).save_mvd3(path, **kwargs)


class CellCollectionComparator(DataframeComparator):
    """Comparator for any type of CellCollection file.

    This comparator inherits from the :class:`dir_content_diff.pandas.DataframeComparator`, read
    the doc of this comparator for details on args and kwargs.
    """

    def load(self, path, **kwargs):
        """Load a CellCollection file into a :class:`pandas.DataFrame`."""
        return CellCollection.load(path, **kwargs).as_dataframe()

    def save(self, data, path, **kwargs):
        """Save data to a CellCollection file."""
        return CellCollection.from_dataframe(data).save(path, **kwargs)


def register():
    """Register Voxcell extensions."""
    register_comparator(".nrrd", NrrdComparator())
    register_comparator(".mvd3", Mvd3Comparator())
