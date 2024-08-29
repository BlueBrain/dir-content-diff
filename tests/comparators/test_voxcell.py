"""Test the Voxcell extension of the ``dir-content-diff`` package."""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=use-implicit-booleaness-not-comparison
import re
import shutil

import numpy as np
import pytest

import dir_content_diff
import dir_content_diff.comparators.voxcell
from dir_content_diff import _DEFAULT_EXPORT_SUFFIX
from dir_content_diff import compare_trees

try:
    import voxcell
except ImportError:
    pass


class TestRegistry:
    """Test the internal registry."""

    def test_voxcell_register(self, registry_reseter):
        assert ".nrrd" not in dir_content_diff.get_comparators()
        assert ".mvd3" not in dir_content_diff.get_comparators()

        dir_content_diff.comparators.voxcell.register()

        assert (
            dir_content_diff.get_comparators()[".nrrd"]
            == dir_content_diff.comparators.voxcell.NrrdComparator()
        )
        assert (
            dir_content_diff.get_comparators()[".mvd3"]
            == dir_content_diff.comparators.voxcell.Mvd3Comparator()
        )


def euler_to_matrix(bank, attitude, heading):
    """Copied from voxcell tests."""

    sa, ca = np.sin(attitude), np.cos(attitude)
    sb, cb = np.sin(bank), np.cos(bank)
    sh, ch = np.sin(heading), np.cos(heading)

    m = np.vstack(
        [
            ch * ca,
            -ch * sa * cb + sh * sb,
            ch * sa * sb + sh * cb,
            sa,
            ca * cb,
            -ca * sb,
            -sh * ca,
            sh * sa * cb + ch * sb,
            -sh * sa * sb + ch * cb,
        ]
    ).transpose()

    return m.reshape(m.shape[:-1] + (3, 3))


def random_orientations(n):
    """Copied from voxcell tests."""
    np.random.seed(0)
    return euler_to_matrix(
        np.random.random(n) * np.pi * 2,
        np.random.random(n) * np.pi * 2,
        np.random.random(n) * np.pi * 2,
    )


def random_positions(n):
    """Copied from voxcell tests."""
    np.random.seed(0)
    return np.random.random((n, 3))


@pytest.fixture
def voxcell_registry_reseter(registry_reseter):
    dir_content_diff.comparators.voxcell.register()


@pytest.fixture
def cell_collection():
    cells = voxcell.cell_collection.CellCollection()
    N = 5

    cells.positions = random_positions(N)
    cells.orientations = random_orientations(N)
    cells.properties["a_property"] = ["val_1", "val_2", "val_3", "val_4", "val_5"]
    cells.properties["another_property"] = ["val_1", "val_2", "val_3", "val_4", "val_5"]
    return cells


@pytest.fixture
def cell_collection_diff(cell_collection):
    cell_collection.positions[:, 0] *= 2
    cell_collection.properties["a_property"] += "_new"
    return cell_collection


@pytest.fixture
def ref_mvd3(empty_ref_tree, cell_collection):
    filename = empty_ref_tree / "file.mvd3"
    cell_collection.save_mvd3(filename)
    return filename


@pytest.fixture
def ref_h5(empty_ref_tree, cell_collection):
    filename = empty_ref_tree / "file.h5"
    cell_collection.save(filename)
    return filename


@pytest.fixture
def res_mvd3_equal(empty_res_tree, ref_mvd3):
    filename = empty_res_tree / "file.mvd3"
    shutil.copyfile(ref_mvd3, filename)
    return filename


@pytest.fixture
def res_h5_equal(empty_res_tree, ref_h5):
    filename = empty_res_tree / "file.h5"
    shutil.copyfile(ref_h5, filename)
    return filename


@pytest.fixture
def res_mvd3_diff(cell_collection_diff, empty_res_tree):
    filename = empty_res_tree / "file.mvd3"
    cell_collection_diff.save_mvd3(filename)
    return filename


@pytest.fixture
def res_h5_diff(cell_collection_diff, empty_res_tree):
    filename = empty_res_tree / "file.h5"
    cell_collection_diff.save(filename)
    return filename


@pytest.fixture
def cell_collection_diff_report():
    return (
        r"""The files '\S*/file.mvd3' and '\S*/file.mvd3' are different:"""
        r"""\n\n"""
        r"""Column 'a_property': Series are different\n"""
        r"""\n"""
        r"""Series values are different \(100.0 %\)\n"""
        r"""\[index\]: \[1, 2, 3, 4, 5\]\n"""
        r"""\[left\]:  \[val_1, val_2, val_3, val_4, val_5\]\n"""
        r"""\[right\]: \[val_1_new, val_2_new, val_3_new, val_4_new, val_5_new\]\n"""
        r"""(At positional index 0, first diff: val_1 != val_1_new\n)?"""
        r"""\n"""
        r"""Column 'x': Series are different\n"""
        r"""\n"""
        r"""Series values are different \(100.0 %\)\n"""
        r"""\[index\]: \[1, 2, 3, 4, 5\]\n"""
        r"""\[left]:  \[0.548813\d+, 0.544883\d+, 0.437587\d+, 0.383441\d+, 0.568044\d+\]\n"""
        r"""\[right]: \[1.097627\d+, 1.089766\d+, 0.875174\d+, 0.766883\d+, 1.136089\d+\]"""
        r"""(At positional index 0, first diff: 0.548813\d+ != 1.097627\d+\n)?"""
    )


@pytest.fixture
def ref_nrrd(empty_ref_tree):
    raw_data = np.array([[[11.1], [12.2]], [[21.3], [22.4]]])
    vd = voxcell.voxel_data.VoxelData(raw_data, (2, 2))
    filename = empty_ref_tree / "file.nrrd"
    vd.save_nrrd(str(filename))
    return filename


@pytest.fixture
def res_nrrd_equal(empty_res_tree, ref_nrrd):
    filename = empty_res_tree / "file.nrrd"
    shutil.copyfile(ref_nrrd, filename)
    return filename


@pytest.fixture
def res_nrrd_diff(empty_res_tree, ref_nrrd):
    # raw_data = np.array([[[11], [12]], [[21], [22]]])
    # vd = voxcell.voxel_data.VoxelData(raw_data, (2, 2))
    vd = voxcell.voxel_data.VoxelData.load_nrrd(ref_nrrd)
    vd.voxel_dimensions += 0.01
    vd.raw += 0.01
    filename = empty_res_tree / "file.nrrd"
    vd.save_nrrd(str(filename))
    return filename


@pytest.fixture
def nrrd_diff():
    return (
        r"""The files '\S*/file.nrrd' and '\S*/file.nrrd' are different:\n"""
        r"""Kwargs used for computing differences: {'precision': None}\n"""
        r"""\n"""
        r"""Voxel dimensions: \n"""
        r"""Arrays are not equal\n"""
        r"""\n"""
        r"""Mismatched elements: 2 / 2 \(100%\)\n"""
        r"""Max absolute difference: 0.00999999\n"""
        r"""Max relative difference: 0.00497512\n"""
        r""" x: array\(\[2., 2.\], dtype=float32\)\n"""
        r""" y: array\(\[2.01, 2.01\], dtype=float32\)\n"""
        r"""\n"""
        r"""Internal raw data: \n"""
        r"""Arrays are not equal\n"""
        r"""\n"""
        r"""Mismatched elements: 4 / 4 \(100%\)\n"""
        r"""Max absolute difference: 0.01\n"""
        r"""Max relative difference: 0.0009\d*\n"""
        r""" x: array\(\[\[\[11.1\],\n"""
        r"""        \[12.2\]\],\n"""
        r"""...\n"""
        r""" y: array\(\[\[\[11.11\],\n"""
        r"""        \[12.21\]\],\n"""
        r"""..."""
    )


class TestEqualTrees:
    """Tests that should return no difference."""

    def test_diff_tree(
        self,
        empty_ref_tree,
        ref_mvd3,
        ref_nrrd,
        empty_res_tree,
        res_mvd3_equal,
        res_nrrd_equal,
        voxcell_registry_reseter,
    ):
        res = compare_trees(empty_ref_tree, empty_res_tree)
        assert res == {}


class TestDiffTrees:
    """Tests that should return differences."""

    def test_diff_tree_mvd3(
        self,
        empty_ref_tree,
        ref_mvd3,
        empty_res_tree,
        res_mvd3_diff,
        cell_collection_diff_report,
        voxcell_registry_reseter,
    ):
        res = compare_trees(
            empty_ref_tree,
            empty_res_tree,
            export_formatted_files=True,
        )
        assert len(res) == 1

        res_mvd3 = res["file.mvd3"]
        match_res = re.match(cell_collection_diff_report, res_mvd3)
        assert match_res is not None

        # Check the saving capability
        assert (
            empty_res_tree.parent / (empty_res_tree.name + _DEFAULT_EXPORT_SUFFIX) / "file.mvd3"
        ).exists()

    def test_diff_tree_h5(
        self,
        empty_ref_tree,
        ref_h5,
        empty_res_tree,
        res_h5_diff,
        cell_collection_diff_report,
        voxcell_registry_reseter,
    ):
        res = compare_trees(
            empty_ref_tree,
            empty_res_tree,
            specific_args={
                "file.h5": {
                    "comparator": dir_content_diff.comparators.voxcell.CellCollectionComparator()
                }
            },
            export_formatted_files=True,
        )
        assert len(res) == 1

        res_h5 = res["file.h5"]
        match_res = re.match(cell_collection_diff_report.replace("mvd3", "h5"), res_h5)
        assert match_res is not None

        # Check the saving capability
        assert (
            empty_res_tree.parent / (empty_res_tree.name + _DEFAULT_EXPORT_SUFFIX) / "file.h5"
        ).exists()

    def test_diff_tree_nrrd(
        self,
        empty_ref_tree,
        ref_nrrd,
        empty_res_tree,
        res_nrrd_diff,
        nrrd_diff,
        voxcell_registry_reseter,
    ):
        res = compare_trees(
            empty_ref_tree,
            empty_res_tree,
            export_formatted_files=True,
        )
        assert len(res) == 1

        res_nrrd = res["file.nrrd"]
        match_res = re.match(nrrd_diff, res_nrrd)
        assert match_res is not None

        # Check the saving capability
        assert (
            empty_res_tree.parent / (empty_res_tree.name + _DEFAULT_EXPORT_SUFFIX) / "file.nrrd"
        ).exists()

    def test_diff_tree_nrrd_precision(
        self,
        empty_ref_tree,
        ref_nrrd,
        empty_res_tree,
        res_nrrd_diff,
        nrrd_diff,
        voxcell_registry_reseter,
    ):
        specific_args = {
            "file.nrrd": {
                "precision": 2,
            }
        }
        res = compare_trees(
            empty_ref_tree,
            empty_res_tree,
            specific_args=specific_args,
            export_formatted_files=True,
        )

        assert len(res) == 0
        assert re.match(".*/file.nrrd.*", str(res)) is None
