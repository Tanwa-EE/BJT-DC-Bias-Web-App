# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web App ที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วคำนวณ DC Operating Point ของวงจร NPN Common-Emitter Voltage-Divider Bias ด้วย Python จริง แสดงผลพร้อมหน่วย มี validation, warning นอก Active Region และ automated tests

**Architecture:** Flask route เดียว (`GET /` + `POST /`) ทำหน้าที่แปลงหน่วยและแปลงข้อความฟอร์มเป็นตัวเลข แล้วเรียกฟังก์ชันบริสุทธิ์ `calculate_dc_bias()` ใน `dc_bias.py` ซึ่งไม่รู้จัก HTML/HTTP; Jinja template แสดงฟอร์มและผลลัพธ์; ไม่มี JavaScript คำนวณใด ๆ

**Tech Stack:** Python 3.14.2, Flask 3.x, Jinja2, `unittest` (stdlib), CSS ธรรมดา (ไม่มี build step)

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## Global Constraints

- Python 3.14.2; dependency เดียวที่อนุญาตคือ **Flask** (ไม่ใช้ WTForms, pytest, numpy, requests)
- รันทุกคำสั่งด้วย `.venv\Scripts\python.exe` (ไม่พึ่ง `python` บน PATH — session นี้ยังถือ PATH เก่าที่ไม่มี Python/Git)
- ค่าที่เก็บใน dict เป็นหน่วย SI (V, A, Ω) เสมอ; การแปลง kΩ → Ω เกิดใน `app.py` เท่านั้น
- การปัดทศนิยมเกิดที่ template เท่านั้น (3 ตำแหน่ง) — ห้ามปัดค่าใน `dc_bias.py`
- ค่าเริ่มต้นของฟอร์มคือค่าตัวอย่างในใบงาน: VCC=12, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70
- UI ภาษาไทย, ชื่อทางเทคนิคเป็นอังกฤษ (VB, VCE, β, RTH)
- **Commit ทำผ่าน GitHub Desktop เท่านั้น** — ขั้น "Commit" ในแผนนี้คือการหยุดและแจ้งผู้ใช้ ไม่ใช่คำสั่ง `git commit`
- เกณฑ์ region: `VTH ≤ VBE` → cutoff, `VCE ≤ 0` → saturation, อื่น ๆ → active (ห้ามใช้เกณฑ์ 0.3 V)

## Review Focus

สิ่งที่สเปกไม่ได้เขียนไว้แต่มีโอกาสทำให้ผู้ใช้เจอปัญหา — แต่ละข้อมี test ใน task ที่รับผิดชอบ:

1. **ส่งฟอร์มโดยเว้นช่องว่าง** — ถ้าใช้ `request.form["vcc"]` ตรง ๆ จะได้ `BadRequestKeyError` → หน้า 500 ผู้ใช้ควรเห็นข้อความบอกว่าช่องไหนว่าง (Task 4)
2. **พิมพ์ `nan` / `inf`** — `float()` ยอมรับทั้งสองค่า ทำให้ผลลัพธ์เป็น `nan` แสดงบนหน้าเว็บโดยไม่มีการเตือน ต้องถูกปฏิเสธพร้อมข้อความ (Task 4)
3. **พิมพ์ตัวเลขติดหน่วยหรือ comma** เช่น `2.2k`, `1,000` — ต้องได้ error ที่บอกว่าไม่ใช่ตัวเลข ไม่ใช่ traceback (Task 4)
4. **`VBE ≥ VCC` หรือ VCC เล็กมาก** — สมการให้ค่าติดลบ/ไร้ความหมายโดยไม่มีใครเตือน ต้องถูกจับที่ validation (Task 1)
5. **β ไม่ใช่จำนวนเต็ม** เช่น 150.5 — ต้องคำนวณได้ตามปกติ ไม่ error (Task 1)

---

### Task 1: Core DC Bias Calculation + Input Validation

**Files:**
- Create: `dc_bias.py`
- Create: `tests/test_dc_bias.py`

**Interfaces:**
- Produces: `calculate_dc_bias(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict`
  - รับหน่วย SI: V, Ω, A (β ไม่มีหน่วย)
  - โยน `ValueError` พร้อมข้อความภาษาไทยเมื่อ: `vcc <= 0`, ตัวต้านทานตัวใดตัวหนึ่ง `<= 0`, `beta <= 0`, หรือไม่ใช่ `0 <= vbe < vcc`
  - คืน dict ที่มีคีย์: `vth`, `rth` (Ω), `ib`, `ic`, `ie` (A), `vb`, `ve`, `vc`, `vce` (V)
  - Task 2 จะเพิ่ม `region`, `warnings`, `ic_sat` เข้าไปใน dict นี้

- [ ] **Step 1: เขียน failing test**

สร้าง `tests/test_dc_bias.py`:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: เขียน `dc_bias.py`**

สร้าง `dc_bias.py` ที่มีฟังก์ชันเดียว `calculate_dc_bias` ตาม signature ข้างต้น ใช้สมการในสเปกข้อ 8 โดยตรง:

- ตรวจ validation ตามลำดับ: VCC → ตัวต้านทานทั้งสี่ → β → VBE ข้อความต้องมีรูปแบบ `<ชื่อฟิลด์> ต้องมากกว่า 0` (เช่น `"R1 ต้องมากกว่า 0"`, `"VCC ต้องมากกว่า 0"`, `"β ต้องมากกว่า 0"`) และกรณี VBE ใช้ `"VBE ต้องอยู่ระหว่าง 0 ถึง VCC"` — Task 4 มี test ที่ตรวจคำว่า `มากกว่า 0`
- `vth = vcc * r2 / (r1 + r2)`, `rth = r1 * r2 / (r1 + r2)`
- `ib = (vth - vbe) / (rth + (beta + 1) * re)`, `ic = beta * ib`, `ie = (beta + 1) * ib`
- `ve = ie * re`, `vb = ve + vbe`, `vc = vcc - ic * rc`, `vce = vc - ve`
- คืน dict 9 คีย์ตามรายการใน Interfaces (ยังไม่ต้องมี region/warnings)
- ห้าม import Flask หรืออ่าน `request` ในไฟล์นี้

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: PASS 6 tests, `OK`

- [ ] **Step 5: หยุด — แจ้งผู้ใช้ commit ผ่าน GitHub Desktop**

ไฟล์: `dc_bias.py`, `tests/test_dc_bias.py`
ข้อความ suggested: `feat: add DC bias calculation with input validation`

---

### Task 2: Region Detection (Cutoff / Saturation) and Warnings

**Files:**
- Modify: `dc_bias.py`
- Modify: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `calculate_dc_bias` จาก Task 1
- Produces: dict เดิม + คีย์เพิ่ม
  - `ic_sat: float` (A) = `vcc / (rc + re)` — คำนวณทุกครั้งไม่ว่า region ใด
  - `region: "active" | "cutoff" | "saturation"`
  - `warnings: list[str]` — `[]` เมื่อ active, 1 ข้อความเมื่อ cutoff หรือ saturation

- [ ] **Step 1: เขียน failing test**

เพิ่มใน `tests/test_dc_bias.py`:

```python
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
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: FAIL — `KeyError: 'region'`

- [ ] **Step 3: เพิ่ม region detection ใน `dc_bias.py`**

หลังคำนวณค่าตามสมการปกติ ให้ทำตามลำดับนี้:

1. คำนวณ `ic_sat = vcc / (rc + re)` เก็บลง dict เสมอ
2. ถ้า `vth <= vbe` → `region = "cutoff"` แล้วเขียนทับ: `ib = ic = ie = 0.0`, `ve = 0.0`, `vb = vth`, `vc = vcc`, `vce = vcc`; warnings = ข้อความที่ระบุค่า VTH และ VBE จริง พร้อมคำว่า `Cutoff`
3. มิฉะนั้นถ้า `vce <= 0` → `region = "saturation"` **ไม่แก้ค่าที่คำนวณได้** (VC/VCE ติดลบได้); warnings = ข้อความระบุว่า VCE ≤ 0, สมการ Forward-Active ใช้ไม่ได้, ทรานซิสเตอร์อิ่มตัว และค่า IC(sat)
4. มิฉะนั้น `region = "active"`, `warnings = []`

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: PASS 9 tests, `OK`

- [ ] **Step 5: หยุด — แจ้งผู้ใช้ commit ผ่าน GitHub Desktop**

ไฟล์: `dc_bias.py`, `tests/test_dc_bias.py`
ข้อความ suggested: `feat: detect cutoff and saturation regions with warnings`

> **Commit checkpoint #1** — หลังขั้นนี้ logic ทั้งหมดถูกทดสอบครบแล้ว

---

### Task 3: Flask Skeleton, Form Page, and Styles

**Files:**
- Create: `requirements.txt`
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate_dc_bias` จาก Task 1–2 (ยังไม่เรียกใน task นี้)
- Produces:
  - module-level `app` (Flask instance) ใน `app.py` — import ได้ด้วย `from app import app`
  - route `GET /` คืน HTML ฟอร์ม
  - ชื่อฟิลด์ฟอร์มที่ Task 4 จะอ่าน: `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`, `unit_r1`, `unit_r2`, `unit_rc`, `unit_re`
  - ค่า dropdown หน่วย: `"kohm"` (ค่าเริ่มต้น) และ `"ohm"`

- [ ] **Step 1: สร้าง venv และติดตั้ง Flask**

Run:
```
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install flask
.venv\Scripts\python.exe -m pip freeze > requirements.txt
```
Expected: `requirements.txt` มี `Flask`, `Jinja2`, `Werkzeug`, `click`, `itsdangerous`, `blinker`, `MarkupSafe` พร้อมเลขเวอร์ชัน

- [ ] **Step 2: เขียน failing test**

สร้าง `tests/test_web.py`:

```python
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
```

- [ ] **Step 3: รัน test ให้เห็นว่า fail**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: สร้าง `app.py` (เฉพาะ GET) และ template**

`app.py`:
- `app = Flask(__name__)`
- `SAMPLE_DEFAULTS` dict เก็บค่าตัวอย่าง (หน่วย kΩ สำหรับตัวต้านทาน)
- `@app.route("/")` เรียก `_render(None, {})` แล้ว return — ยังไม่เรียก `calculate_dc_bias`
- ฟังก์ชัน `_render(result, form_values, errors=None)` เรียก `render_template("index.html", ...)`
- ไม่มีสมการในไฟล์นี้

`templates/index.html`:
- `<form method="post" action="/">` มี input 7 ช่อง (number, step="any") + select หน่วย 4 ตัว
- ทุก input ต้องมี `name=` ตรงตาม Interfaces; ค่าเริ่มต้นมาจาก `form_values`
- **ห้ามมีข้อความ "VCE"** ในหน้านี้ตอนยังไม่มีผลลัพธ์ (test ที่ 4 บังคับ)
- ลิงก์ CSS ด้วย `url_for('static', filename='style.css')`

`static/style.css`: จัดหน้า 2 คอลัมน์ (ฟอร์ม | พื้นที่ผลลัพธ์) บนจอ ≥ 900px และคอลัมน์เดียวบนมือถือ

- [ ] **Step 5: รัน test ให้ผ่าน**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: PASS 4 tests, `OK`

- [ ] **Step 6: หยุด — แจ้งผู้ใช้ commit ผ่าน GitHub Desktop**

ไฟล์: `requirements.txt`, `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`
ข้อความ suggested: `feat: add Flask form page and styles`

---

### Task 4: POST /calculate — Parsing, Unit Conversion, Results, and Errors

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate_dc_bias` (Task 1–2), ฟิลด์ฟอร์มและ `app` (Task 3)
- Produces:
  - `POST /` คืน **HTTP 200 เสมอ** (ทั้งสำเร็จและ error)
  - `_parse_length(form, name: str) -> float` — อ่าน `name` + `unit_<name>` แล้วคืนค่าเป็น Ω; โยน `ValueError` พร้อมข้อความภาษาไทยถ้าช่องว่าง / ไม่ใช่ตัวเลข / ไม่ finite / ค่า ≤ 0 / หน่วยไม่รู้จัก
  - `_parse_number(form, name: str) -> float` — สำหรับ `vcc`, `beta`, `vbe`; โยน `ValueError` ด้วยเงื่อนไขเดียวกัน (ยกเว้นเงื่อนไข ≤ 0 ซึ่งปล่อยให้ `calculate_dc_bias` ตรวจ)

- [ ] **Step 1: เขียน failing test**

เพิ่มใน `tests/test_web.py`:

```python
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
        self.assertIn("8.052", html)      # VCE
        self.assertIn("1.230", html)      # IC [mA]
        self.assertIn("1.942", html)      # VB

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
        html = resp.get_data(as_text=True)
        self.assertIn("มากกว่า 0", html)

    def test_saturation_shows_warning(self):
        resp = self.post(rc="15")
        html = resp.get_data(as_text=True)
        self.assertIn("อิ่มตัว", html)

    def test_cutoff_shows_warning(self):
        resp = self.post(r2="5")
        html = resp.get_data(as_text=True)
        self.assertIn("Cutoff", html)

    def test_entered_values_are_kept_on_error(self):
        html = self.post(vcc="abc", r1="47").get_data(as_text=True)
        self.assertIn('value="47"', html)
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL หลายตัว — POST ยังไม่ถูกจัดการ (`405 Method Not Allowed` หรือ assertion error)

- [ ] **Step 3: เพิ่ม POST handling ใน `app.py`**

- `@app.route("/", methods=["GET", "POST"])`
- บน POST: วนอ่านทุกฟิลด์ด้วย `_parse_length` / `_parse_number` เก็บ `ValueError` ทั้งหมดไว้ใน `errors` list (ไม่หยุดที่ error แรก เพื่อให้ผู้ใช้เห็นครบ)
- ถ้า `errors` ไม่ว่าง → `_render(None, form_values, errors)` และ return (HTTP 200)
- ถ้าผ่าน → เรียก `calculate_dc_bias(...)` ใน `try/except ValueError` (ข้อความจาก validation ของ Task 1 ไปเข้า `errors`)
- สำเร็จ → `_render(result, form_values, None)`
- `form_values` ต้องคงค่าดิบที่ผู้ใช้พิมพ์ (string) เพื่อ sticky form
- ข้อความ error จากตัวแปลงค่าต้องมีคำเหล่านี้ (test ตรวจ): ช่องว่าง → `"กรุณากรอก"`; แปลงไม่ได้ / `nan` / `inf` → `"ไม่ใช่ตัวเลข"`; ค่า ≤ 0 → `"มากกว่า 0"`; หน่วยไม่รู้จัก → `"หน่วยของ"`

- [ ] **Step 4: เพิ่มส่วนผลลัพธ์ใน `templates/index.html`**

- กล่อง error (แดง) แสดงทีละบรรทัดจาก `errors`
- เมื่อมี `result`: ป้าย Region, กล่อง warning (ส้ม) จาก `result.warnings`, ตารางผลลัพธ์
  - แถว: VTH [V], RTH [kΩ], VB [V], VE [V], VC [V], VCE [V], IC [mA], IB [µA], IE [mA]
  - แถว `IC(sat) [mA]` แสดงเฉพาะเมื่อ `result.region == "saturation"`
  - ใช้ filter `"%.3f"|format(...)` ในการปัด — ห้ามปัดใน Python ก่อนส่งเข้า template
- ห้ามมีสมการในไฟล์นี้

- [ ] **Step 5: รัน test ให้ผ่าน**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS 23 tests, `OK` (9 จาก `test_dc_bias.py` + 14 จาก `test_web.py`)

- [ ] **Step 6: หยุด — แจ้งผู้ใช้ commit ผ่าน GitHub Desktop**

ไฟล์: `app.py`, `templates/index.html`, `tests/test_web.py`
ข้อความ suggested: `feat: calculate and render DC bias results with validation`

> **Commit checkpoint #2** — เว็บใช้งานได้ครบตาม acceptance A1–A6 แล้ว

---

### Task 5: Documentation and End-to-End Verification

**Files:**
- Create: `README.md`
- Create: `docs/validation.md`
- Create: `docs/design-note.md`
- Create: `docs/reflection.md` (โครงให้ผู้ใช้เขียนต่อ)

**Interfaces:**
- Consumes: ทุกอย่างจาก Task 1–4
- Produces: เอกสารที่ทำให้คนอื่น clone แล้วรันได้ (accepted A7)

- [ ] **Step 1: เขียน `docs/validation.md`**

ตารางค่าอ้างอิงจากการคำนวณมือ (คัดลอกจากสเปกข้อ 12) พร้อมแสดงสมการที่ใช้และผลลัพธ์จริงจากโปรแกรมวางเทียบกัน:

| ปริมาณ | คำนวณมือ | โปรแกรม |
|---|---|---|
| VTH | 2.1639 V | (เติมจากผลรัน) |
| RTH | 18.0328 kΩ | |
| IB | 12.299 µA | |
| IC | 1.2299 mA | |
| IE | 1.2422 mA | |
| VE | 1.2422 V | |
| VB | 1.9422 V | |
| VC | 9.2943 V | |
| VCE | 8.0522 V | |

เพิ่มกรณี cutoff (R2 = 5 kΩ, VTH = 0.571 V) และ saturation (RC = 15 kΩ, VC = −6.4479 V, VCE = −7.6900 V, IC(sat) = 0.750 mA) พร้อมข้อความว่าเหตุใดค่าเหล่านี้จึงไม่ควรเชื่อถือ

- [ ] **Step 2: เขียน `docs/design-note.md`** (1 หน้า)

อธิบาย: การแยก `app.py` / `dc_bias.py` / template / static / tests, contract ของ `calculate_dc_bias`, เหตุผลที่เลือกทาง A (route เดียว) และสิ่งที่จงใจไม่ทำ (AC, SPICE, bias แบบอื่น)

- [ ] **Step 3: เขียน `README.md`**

ต้องมีครบ 5 หัวข้อ:
1. ต้องมีอะไรในเครื่อง (Python 3.x)
2. สร้าง venv + ติดตั้ง dependency (`py -m venv .venv`, `.venv\Scripts\python.exe -m pip install -r requirements.txt`)
3. รันเว็บ (`.venv\Scripts\python.exe -m flask --app app run --debug`) + เปิด `http://127.0.0.1:5000/`
4. รัน tests (`.venv\Scripts\python.exe -m unittest discover -s tests -v`)
5. สมมติฐานและข้อจำกัด: Forward-Active, β และ VBE คงที่, ไม่ใช่ SPICE, ผลนอก Active Region เป็นเพียงการประมาณ

- [ ] **Step 4: สร้าง `docs/reflection.md` เป็นโครง**

หัวข้อให้ผู้ใช้เติมเอง: อะไรที่ AI ช่วยได้/ไม่ได้, จุดที่ต้องตรวจสอบผลคำนวณเอง, ถ้าจะทำ Week 3 ต่อจะเริ่มจากตรงไหน

- [ ] **Step 5: รัน test ทั้งหมดและบันทึกผล**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS 23 tests, `OK` — คัดลอก output เก็บไว้เป็นหลักฐานส่งงาน

- [ ] **Step 6: ตรวจ reproduction จากศูนย์**

Run (ใน PowerShell หน้าต่างใหม่, โฟลเดอร์ repo):
```
Remove-Item -Recurse -Force .venv
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
```
Expected: ติดตั้งสำเร็จและ test ผ่านทั้ง 23 ตัว — ยืนยันว่า README/requirements ครบ (A7)

- [ ] **Step 7: หยุด — แจ้งผู้ใช้ทำ demo และ commit**

ให้ผู้ใช้:
1. รัน `.venv\Scripts\python.exe -m flask --app app run --debug` แล้วเปิด `http://127.0.0.1:5000/`
2. กรอกค่าตัวอย่าง → เห็น VCE ≈ 8.052 V, IC ≈ 1.230 mA
3. ลอง `R1 = 0` → เห็น error; ลอง `RC = 15` → เห็น warning อิ่มตัว
4. จับภาพหน้าจอ + คัดลอก test log
5. Commit ผ่าน GitHub Desktop: `docs: add README and validation notes` (ไฟล์: `README.md`, `docs/validation.md`, `docs/design-note.md`, `docs/reflection.md`)

> **Commit checkpoint #3** — พร้อมส่งงาน

---

## Self-Review

- **Spec coverage:** A1 (Task 3), A2 (Task 4), A3 (Task 1 + Task 5 validation.md), A4 (Task 1 + Task 4), A5 (Task 2 + Task 4), A6 (Task 1–4), A7 (Task 5) — ครบ
- **Type consistency:** `calculate_dc_bias(...)` คืน dict คีย์เดียวกับที่ template และ test อ้างถึง (`vth`, `rth`, `ib`, `ic`, `ie`, `vb`, `ve`, `vc`, `vce`, `ic_sat`, `region`, `warnings`); ชื่อฟิลด์ฟอร์มตรงกันระหว่าง Task 3 (สร้าง) และ Task 4 (อ่าน)
- **Review Focus:** ทั้ง 5 ข้อมี test ใน task ที่ระบุ (ข้อ 1, 2, 3 → Task 4; ข้อ 4, 5 → Task 1)
