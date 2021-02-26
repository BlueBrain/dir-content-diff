"""Extension module to process files with Voxcell."""
import numpy as np

try:
    from voxcell import CellCollection
    from voxcell import VoxelData
except ImportError as e:  # pragma: no cover
    raise ImportError("Could not import voxcell package, please install it.") from e

from dir_content_diff import register_comparator
from dir_content_diff.pandas import compare_dataframes
from dir_content_diff.util import diff_msg_formatter


def compare_nrrd_files(ref_path, comp_path, precision=None):
    """Compare data from two NRRD files.

    Note: NRRD files can contain their creation date, so their hashes are depends on
    this creation date, even if the data are the same.

    Args:
        ref_path (str): The path to the reference CSV file.
        comp_path (str): The path to the compared CSV file.
        precision (int): The desired precision, default is 6.

    Returns:
        bool or str: ``True`` if the DataFrames are considered as equal or a string explaining why
        they are not considered as equal.
    """
    ref = VoxelData.load_nrrd(ref_path).raw
    comp = VoxelData.load_nrrd(comp_path).raw
    try:
        if precision is not None:
            np.testing.assert_array_almost_equal(ref, comp, decimal=precision)
        else:
            np.testing.assert_array_equal(ref, comp)
        return True
    except AssertionError as exception:
        return diff_msg_formatter(
            ref_path, comp_path, exception.args[0], kwargs={"precision": precision}
        )


def compare_mvd3_files(ref_path, comp_path, *args, **kwargs):
    """Compare data from two MVD3 files.

    Note: MVD3 files can contain their creation date, so their hashes are depends on
    this creation date, even if the data are the same.

    This function calls :func:`dir_content_diff.pandas.compare_dataframes`, read the doc of this
    function for details on args and kwargs.

    Args:
        ref_path (str): The path to the reference CSV file.
        comp_path (str): The path to the compared CSV file.

    Returns:
        bool or str: ``True`` if the DataFrames are considered as equal or a string explaining why
        they are not considered as equal.
    """
    ref = CellCollection.load_mvd3(ref_path).as_dataframe()
    comp = CellCollection.load_mvd3(comp_path).as_dataframe()
    res = compare_dataframes(ref, comp, *args, **kwargs)
    return diff_msg_formatter(ref_path, comp_path, res, args, kwargs)


def register_voxcell():
    """Register Voxcell extensions."""
    register_comparator(".nrrd", compare_nrrd_files)
    register_comparator(".mvd3", compare_mvd3_files)
