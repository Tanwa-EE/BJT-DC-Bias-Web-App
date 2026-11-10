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


if __name__ == "__main__":
    unittest.main()
