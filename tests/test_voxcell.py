"""Test the Voxcell extension of the dir-content-diff package."""
# pylint: disable=missing-function-docstring
# pylint: disable=no-self-use
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import re
import shutil

import numpy as np
import pytest
import voxcell

import dir_content_diff
import dir_content_diff.voxcell
from dir_content_diff import compare_trees


class TestRegistry:
    """Test the internal registry."""

    def test_voxcell_register(self, registry_reseter):
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".xml": dir_content_diff.XmlComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
        }

        dir_content_diff.voxcell.register_voxcell()
        assert dir_content_diff.get_comparators() == {
            None: dir_content_diff.DefaultComparator(),
            ".json": dir_content_diff.JsonComparator(),
            ".pdf": dir_content_diff.PdfComparator(),
            ".xml": dir_content_diff.XmlComparator(),
            ".yaml": dir_content_diff.YamlComparator(),
            ".yml": dir_content_diff.YamlComparator(),
            ".nrrd": dir_content_diff.voxcell.NrrdComparator(),
            ".mvd3": dir_content_diff.voxcell.Mvd3Comparator(),
        }


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
    dir_content_diff.voxcell.register_voxcell()


@pytest.fixture
def ref_mvd3(ref_tree):
    cells = voxcell.cell_collection.CellCollection()
    N = 5

    cells.positions = random_positions(N)
    cells.orientations = random_orientations(N)
    cells.properties["a_property"] = ["val_1", "val_2", "val_3", "val_4", "val_5"]
    cells.properties["another_property"] = ["val_1", "val_2", "val_3", "val_4", "val_5"]

    filename = ref_tree / "file.mvd3"
    cells.save_mvd3(filename)

    return filename


@pytest.fixture
def res_mvd3_equal(res_tree_equal, ref_mvd3):
    filename = res_tree_equal / "file.mvd3"
    shutil.copyfile(ref_mvd3, filename)
    return filename


@pytest.fixture
def res_mvd3_diff(ref_mvd3, res_tree_diff):
    data = voxcell.cell_collection.CellCollection.load_mvd3(ref_mvd3)
    data.positions[:, 0] *= 2
    data.properties["a_property"] += "_new"
    filename = res_tree_diff / "file.mvd3"
    data.save_mvd3(filename)
    return filename


@pytest.fixture
def mvd3_diff():
    return (
        r"""The files '\S*/file.mvd3' and '\S*/file.mvd3' are different:"""
        r"""\n\n"""
        r"""Column 'a_property': Series are different\n"""
        r"""\n"""
        r"""Series values are different \(100.0 %\)\n"""
        r"""\[index\]: \[1, 2, 3, 4, 5\]\n"""
        r"""\[left\]:  \[val_1, val_2, val_3, val_4, val_5\]\n"""
        r"""\[right\]: \[val_1_new, val_2_new, val_3_new, val_4_new, val_5_new\]\n"""
        r"""\n"""
        r"""Column 'x': Series are different\n"""
        r"""\n"""
        r"""Series values are different \(100.0 %\)\n"""
        r"""\[index\]: \[1, 2, 3, 4, 5\]\n"""
        r"""\[left]:  \[0.548813\d+, 0.544883\d+, 0.437587\d+, 0.383441\d+, 0.568044\d+\]\n"""
        r"""\[right]: \[1.097627\d+, 1.089766\d+, 0.875174\d+, 0.766883\d+, 1.136089\d+\]"""
    )


@pytest.fixture
def ref_nrrd(ref_tree):
    raw_data = np.array([[[11.1], [12.2]], [[21.3], [22.4]]])
    vd = voxcell.voxel_data.VoxelData(raw_data, (2, 2))
    filename = ref_tree / "file.nrrd"
    vd.save_nrrd(str(filename))
    return filename


@pytest.fixture
def res_nrrd_equal(res_tree_equal, ref_nrrd):
    filename = res_tree_equal / "file.nrrd"
    shutil.copyfile(ref_nrrd, filename)
    return filename


@pytest.fixture
def res_nrrd_diff(res_tree_diff, ref_nrrd):
    # raw_data = np.array([[[11], [12]], [[21], [22]]])
    # vd = voxcell.voxel_data.VoxelData(raw_data, (2, 2))
    vd = voxcell.voxel_data.VoxelData.load_nrrd(ref_nrrd)
    vd.raw += 0.01
    filename = res_tree_diff / "file.nrrd"
    vd.save_nrrd(str(filename))
    return filename


@pytest.fixture
def nrrd_diff():
    return (
        r"""The files '\S*/file.nrrd' and '\S*/file.nrrd' are different:\n"""
        r"""Kwargs used: {'precision': None}\n"""
        r"""\n"""
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
        ref_tree,
        ref_mvd3,
        ref_nrrd,
        res_tree_equal,
        res_mvd3_equal,
        res_nrrd_equal,
        voxcell_registry_reseter,
    ):
        res = compare_trees(ref_tree, res_tree_equal)
        assert res == {}


class TestDiffTrees:
    """Tests that should return differences."""

    def test_diff_tree_mvd3(
        self, ref_tree, ref_mvd3, res_tree_diff, res_mvd3_diff, mvd3_diff, voxcell_registry_reseter
    ):
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 5
        res_mvd3 = res["file.mvd3"]
        match_res = re.match(mvd3_diff, res_mvd3)
        assert match_res is not None

    def test_diff_tree_nrrd(
        self, ref_tree, ref_nrrd, res_tree_diff, res_nrrd_diff, nrrd_diff, voxcell_registry_reseter
    ):
        res = compare_trees(ref_tree, res_tree_diff)

        assert len(res) == 5
        res_nrrd = res["file.nrrd"]
        match_res = re.match(nrrd_diff, res_nrrd)
        assert match_res is not None

    def test_diff_tree_nrrd_precision(
        self, ref_tree, ref_nrrd, res_tree_diff, res_nrrd_diff, nrrd_diff, voxcell_registry_reseter
    ):
        specific_args = {
            "file.nrrd": {
                "kwargs": {
                    "precision": 2,
                }
            }
        }
        res = compare_trees(ref_tree, res_tree_diff, specific_args=specific_args)

        assert len(res) == 4
        assert re.match(".*/file.nrrd.*", str(res)) is None
