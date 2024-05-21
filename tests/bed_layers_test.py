from unittest import TestCase

import pandas as pd
from pandas.testing import assert_frame_equal

from collector_sed.sed_model import cut_sedbed, cut_settled_only


class TestBedLayersCutting(TestCase):
    # def assertDataframeEqual(self, a, b, msg):
    #     try:
    #         pd_testing.assert_frame_equal(a, b)
    #     except AssertionError as e:
    #         raise self.failureException(msg) from e

    def test_cut_only_bed(self):
        CUT = 0.1

        bed_layers = pd.DataFrame(
            {
                "top": [0.0],
                "bottom": [-0.2],
                "type": ["bed"],
                "name": ["existing"],
            }
        )

        correct_layers = pd.DataFrame(
            {
                "top": [0.0 - CUT],
                "bottom": [-0.2],
                "type": ["bed"],
                "name": ["existing"],
            }
        )

        new_bed_layers, cut_bed, cut_settled = cut_sedbed(bed_layers, CUT)
        self.assertAlmostEqual(cut_bed, CUT)
        self.assertAlmostEqual(cut_settled, 0.0)
        assert_frame_equal(new_bed_layers, correct_layers)

        bed_layers = pd.DataFrame(
            {
                "top": [0.5],
                "bottom": [-0.2],
                "type": ["bed"],
                "name": ["existing"],
            }
        )

        correct_layers = pd.DataFrame(
            {
                "top": [0.5 - CUT],
                "bottom": [-0.2],
                "type": ["bed"],
                "name": ["existing"],
            }
        )

        new_bed_layers, cut_bed, cut_settled = cut_sedbed(bed_layers, CUT)
        self.assertAlmostEqual(cut_bed, CUT)
        self.assertAlmostEqual(cut_settled, 0.0)
        assert_frame_equal(new_bed_layers, correct_layers)

    def test_cut_with_one_settled(self):
        CUT = 0.1

        bed_layers = pd.DataFrame(
            {
                "top": [0.2, 0.0],
                "bottom": [0.0, -0.2],
                "type": ["settled", "bed"],
                "name": ["0", "existing"],
            }
        )

        correct_layers = pd.DataFrame(
            {
                "top": [0.1, 0.0],
                "bottom": [0.0, -0.2],
                "type": ["settled", "bed"],
                "name": ["0", "existing"],
            }
        )

        new_bed_layers, cut_bed, cut_settled = cut_sedbed(bed_layers, CUT)
        self.assertAlmostEqual(cut_bed, 0.0)
        self.assertAlmostEqual(cut_settled, CUT)
        assert_frame_equal(new_bed_layers, correct_layers)

        bed_layers = pd.DataFrame(
            {
                "top": [-0.2, -0.5],
                "bottom": [-0.5, -0.8],
                "type": ["settled", "bed"],
                "name": ["0", "existing"],
            }
        )

        correct_layers = pd.DataFrame(
            {
                "top": [-0.2 - CUT, -0.5],
                "bottom": [-0.5, -0.8],
                "type": ["settled", "bed"],
                "name": ["0", "existing"],
            }
        )

        new_bed_layers, cut_bed, cut_settled = cut_sedbed(bed_layers, CUT)
        self.assertAlmostEqual(cut_bed, 0.0)
        self.assertAlmostEqual(cut_settled, CUT)
        assert_frame_equal(new_bed_layers, correct_layers)

    def test_cut_with_multiple_settled(self):
        CUT = 0.1

        bed_layers = pd.DataFrame(
            {
                "top": [0.5, 0.4, 0.2, 0.0],
                "bottom": [0.4, 0.2, 0.0, -0.5],
                "type": ["settled", "settled", "settled", "bed"],
                "name": ["2", "1", "0", "existing"],
            }
        )

        correct_layers = pd.DataFrame(
            {
                "top": [0.4, 0.2, 0.0],
                "bottom": [0.2, 0.0, -0.5],
                "type": ["settled", "settled", "bed"],
                "name": ["1", "0", "existing"],
            }
        )

        new_bed_layers, cut_bed, cut_settled = cut_sedbed(bed_layers, CUT)
        self.assertAlmostEqual(cut_bed, 0.0)
        self.assertAlmostEqual(cut_settled, CUT)
        assert_frame_equal(new_bed_layers, correct_layers)

class TestCutSettled(TestCase):
    def test_cut_with_multiple_settled(self):
        CUT = 0.1

        bed_layers = pd.DataFrame(
            {
                "top": [0.5, 0.38, 0.2, 0.0],
                "bottom": [0.38, 0.2, 0.0, -0.5],
                "type": ["settled", "settled", "settled", "bed"],
                "name": ["2", "1", "0", "existing"],
            }
        )

        correct_layers = pd.DataFrame(
            {
                "top": [0.4, 0.38, 0.2, 0.0],
                "bottom": [0.38, 0.2, 0.0, -0.5],
                "type": ["settled", "settled", "settled", "bed"],
                "name": ["2", "1", "0", "existing"],
            }
        )

        new_bed_layers, cut_settled = cut_settled_only(bed_layers, CUT)
        self.assertAlmostEqual(cut_settled, CUT)
        assert_frame_equal(new_bed_layers, correct_layers)
        
        
    def test_cut_with_thin_settled(self):
        
        CUT = 0.1
        
        bed_layers = pd.DataFrame(
            {
                "top": [0.0245, 0.0],
                "bottom": [0.0, -0.5],
                "type": ["settled", "bed"],
                "name": ["0", "existing"],
            }
        )

        correct_layers = pd.DataFrame(
            {
                "top": [0.0],
                "bottom": [-0.5],
                "type": ["bed"],
                "name": ["existing"],
            }
        )

        new_bed_layers, cut_settled = cut_settled_only(bed_layers, CUT)
        self.assertAlmostEqual(cut_settled, 0.0245)
        assert_frame_equal(new_bed_layers, correct_layers)
        