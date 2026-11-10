import unittest

from dc_bias import calculate_dc_bias

SAMPLE = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
              re=1_000.0, beta=100.0, vbe=0.70)


class TestActiveRegion(unittest.TestCase):
    def test_sample_bias_point(self):
        r = calculate_dc_bias(**SAMPLE)
        self.assertAlmostEqual(r["vth"], 2.1639, places=3)
        self.assertAlmostEqual(r["rth"], 18_032.787, delta=1.0)
        self.assertAlmostEqual(r["ib"] * 1e6, 12.299, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.2299, places=3)
        self.assertAlmostEqual(r["ie"] * 1e3, 1.2422, places=3)
        self.assertAlmostEqual(r["ve"], 1.2422, places=3)
        self.assertAlmostEqual(r["vb"], 1.9422, places=3)
        self.assertAlmostEqual(r["vc"], 9.2943, places=3)
        self.assertAlmostEqual(r["vce"], 8.0522, places=3)

    def test_fractional_beta_is_accepted(self):
        r = calculate_dc_bias(**{**SAMPLE, "beta": 150.5})
        self.assertGreater(r["ic"], 0.0)


class TestValidation(unittest.TestCase):
    def test_zero_resistor_raises(self):
        for key in ("r1", "r2", "rc", "re"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    calculate_dc_bias(**{**SAMPLE, key: 0.0})

    def test_non_positive_beta_raises(self):
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**SAMPLE, "beta": 0.0})

    def test_vcc_zero_raises(self):
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**SAMPLE, "vcc": 0.0})

    def test_vbe_not_below_vcc_raises(self):
        with self.assertRaises(ValueError):
            calculate_dc_bias(**{**SAMPLE, "vbe": 12.0})


class TestRegionDetection(unittest.TestCase):
    def test_active_region_has_no_warning(self):
        r = calculate_dc_bias(**SAMPLE)
        self.assertEqual(r["region"], "active")
        self.assertEqual(r["warnings"], [])
        self.assertAlmostEqual(r["ic_sat"] * 1e3, 3.75, places=4)

    def test_cutoff_region(self):
        r = calculate_dc_bias(**{**SAMPLE, "r2": 5_000.0})
        self.assertEqual(r["region"], "cutoff")
        self.assertEqual(r["ib"], 0.0)
        self.assertEqual(r["ic"], 0.0)
        self.assertEqual(r["ie"], 0.0)
        self.assertAlmostEqual(r["vb"], 0.5714, places=3)
        self.assertAlmostEqual(r["vc"], 12.0, places=3)
        self.assertAlmostEqual(r["vce"], 12.0, places=3)
        self.assertEqual(len(r["warnings"]), 1)
        self.assertIn("Cutoff", r["warnings"][0])

    def test_saturation_region(self):
        r = calculate_dc_bias(**{**SAMPLE, "rc": 15_000.0})
        self.assertEqual(r["region"], "saturation")
        self.assertAlmostEqual(r["ic_sat"] * 1e3, 0.75, places=4)
        self.assertAlmostEqual(r["vc"], -6.4479, places=3)
        self.assertAlmostEqual(r["vce"], -7.6900, places=3)
        self.assertEqual(len(r["warnings"]), 1)


if __name__ == "__main__":
    unittest.main()
