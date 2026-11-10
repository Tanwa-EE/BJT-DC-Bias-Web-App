import unittest

from app import app


class TestFormPage(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_form_returns_200(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_form_has_all_fields(self):
        html = self.client.get("/").get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', html)
        for field in ("unit_r1", "unit_r2", "unit_rc", "unit_re"):
            self.assertIn(f'name="{field}"', html)

    def test_form_prefilled_with_sample_values(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('value="100"', html)
        self.assertIn('value="22"', html)
        self.assertIn('value="12"', html)

    def test_no_results_before_calculate(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("VCE", html)


class TestCalculatePage(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def post(self, **overrides):
        data = dict(vcc="12", r1="100", r2="22", rc="2.2", re="1",
                    beta="100", vbe="0.7",
                    unit_r1="kohm", unit_r2="kohm",
                    unit_rc="kohm", unit_re="kohm")
        data.update(overrides)
        return self.client.post("/", data=data)

    def test_sample_values_render_results(self):
        resp = self.post()
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("8.052", html)
        self.assertIn("1.230", html)
        self.assertIn("1.942", html)

    def test_unit_conversion_ohm_matches_kohm(self):
        resp = self.post(r1="100000", r2="22000", rc="2200", re="1000",
                         unit_r1="ohm", unit_r2="ohm",
                         unit_rc="ohm", unit_re="ohm")
        self.assertIn("8.052", resp.get_data(as_text=True))

    def test_missing_field_shows_error_not_crash(self):
        resp = self.post(vcc="")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("กรุณากรอก", resp.get_data(as_text=True))

    def test_non_numeric_shows_error(self):
        resp = self.post(vcc="abc")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ไม่ใช่ตัวเลข", resp.get_data(as_text=True))

    def test_unit_suffix_shows_error(self):
        resp = self.post(rc="2.2k")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ไม่ใช่ตัวเลข", resp.get_data(as_text=True))

    def test_nan_is_rejected(self):
        resp = self.post(vcc="nan")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ไม่ใช่ตัวเลข", resp.get_data(as_text=True))

    def test_zero_resistor_shows_error(self):
        resp = self.post(r1="0")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("มากกว่า 0", resp.get_data(as_text=True))

    def test_saturation_shows_warning(self):
        resp = self.post(rc="15")
        self.assertIn("อิ่มตัว", resp.get_data(as_text=True))

    def test_cutoff_shows_warning(self):
        resp = self.post(r2="5")
        self.assertIn("Cutoff", resp.get_data(as_text=True))

    def test_entered_values_are_kept_on_error(self):
        html = self.post(vcc="abc", r1="47").get_data(as_text=True)
        self.assertIn('value="47"', html)


if __name__ == "__main__":
    unittest.main()
