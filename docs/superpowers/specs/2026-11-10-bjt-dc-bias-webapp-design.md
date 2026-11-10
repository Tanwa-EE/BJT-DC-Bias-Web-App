# Design — BJT DC Bias Web App (ENG29 2121 Lab 02)

- วันที่: 2026-11-10
- สถานะ: รออนุมัติ
- เจ้าของงาน: Tanwa (นักศึกษา)

## 1. บริบทและเหตุผล

Lab 02 ของรายวิชา ENG29 2121 ต้องการให้นักศึกษาเห็นว่า Web Application จริงประกอบขึ้นจาก
Frontend (Template/CSS), HTTP Routing, Backend Logic และ Automated Tests ที่แยกจากกัน
ไม่ใช่ HTML ไฟล์เดียวที่ฝังตัวเลข计算结果 ไว้

ผลงานคือ Flask Web App ที่รับค่าอุปกรณ์ของวงจร NPN Common-Emitter แบบ Voltage-Divider Bias
แล้วให้ Python คำนวณ DC Operating Point จริง ส่งกลับมาแสดงในหน้าเว็บ

## 2. Goals

| # | เป้าหมาย | ตรวจได้ด้วย |
|---|----------|-------------|
| G1 | `GET /` คืน HTTP 200 และแสดงฟอร์ม | Flask test client + เปิด browser |
| G2 | `POST /` รับค่าและให้ **Python** คำนวณ | ผลเปลี่ยนตามอินพุต ไม่ใช่ค่าคงที่ |
| G3 | ค่าที่ได้ตรงกับสมการ forward-active | เทียบกับค่าคำนวณมือ (ข้อ 7) |
| G4 | อินพุตผิดแสดง error ที่อ่านได้ ไม่ crash | รันกรณีผิดใน browser + test |
| G5 | แจ้ง Warning เมื่ออยู่นอก Active Region | กรณี cutoff / saturation |
| G6 | มี automated tests | ≥3 test ด้านสมการ + ≥1 test ผ่าน Flask client |
| G7 | รันซ้ำได้ตาม README | clone → venv → run → test |

## 3. Non-goals (ไม่ทำใน Lab นี้)

- AC small-signal, Gain, Bode plot, Transient
- Bias แบบอื่น (Fixed, Emitter) — เก็บไว้ Week 3
- SPICE / ngspice, DC Load Line
- ระบบ login, ฐานข้อมูล, การ deploy ขึ้นเซิร์ฟเวอร์สาธารณะ
- Interactive schematic / animation

## 4. Anti-goals (ถ้าเกิดขึ้น ถือว่างานล้มเหลวแม้จะรันได้)

- ตัวเลข DC Bias ถูก hardcode ไว้ใน HTML หรือ JavaScript
- สมการฟิสิกส์อยู่ใน template หรือใน `app.py`
- เปิดด้วย `file://` แล้วใช้งานได้ (ต้องผ่าน Flask server เท่านั้น)
- Test ที่ไม่ได้รันจริง หรือรายงานว่า "ผ่าน" โดยไม่มี log
- Commit `.venv/`, `__pycache__/`, `.env` หรือ credential ใด ๆ

## 5. Constraints

- Python 3.14.2 (เครื่องผู้พัฒนา), Flask 3.x ภายใน `.venv`
- Windows 11 + PowerShell, รันที่ `http://127.0.0.1:5000/`
- เวลาสร้าง ~75 นาที, ทั้งคาบ 180 นาที
- dependency: Flask เท่านั้น + stdlib (`unittest`, `dataclasses`) — ไม่ใช้ WTForms/numpy/pytest
- UI ภาษาไทย เก็บชื่อทางเทคนิคเป็นอังกฤษ (VB, VCE, β)
- Commit/Push ทำผ่าน **GitHub Desktop** เท่านั้น (ไม่ใช้คำสั่ง git ใน terminal)

## 6. Approaches ที่พิจารณา

| ทาง | ลักษณะ | ผล |
|-----|--------|-----|
| **A (เลือก)** | route เดียว `GET/POST /`, `dc_bias.py` เป็นฟังก์ชันบริสุทธิ์, Jinja render, `unittest` | โค้ดน้อย ทดสอบง่าย แยกชั้นชัด |
| B | `/api/calculate` คืน JSON + fetch ในหน้าเว็บ | UX ลื่นกว่า แต่ JS เพิ่ม error handling สองชั้น และ test ด้วย Flask client ครอบคลุมได้น้อย |
| C | `POST /calculate` → redirect (PRG) | HTTP ถูกต้องสุด แต่ต้องเก็บ state เพิ่ม งานงอกโดยไม่ได้คะแนนเพิ่ม |

เลือก **A** เพราะ Scope คือ "smallest working app" และคะแนนวัดที่การแยก Backend/Template/Test
ไม่ใช่ความลื่นของ UI

## 7. โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py                      # Flask routes, parsing, unit conversion, error surfacing
├── dc_bias.py                  # สมการ + region detection (ไม่รู้จัก HTML/HTTP)
├── templates/
│   └── index.html              # ฟอร์ม + ผลลัพธ์ + warning (Jinja2)
├── static/
│   └── style.css               # responsive layout
├── tests/
│   ├── test_dc_bias.py         # unit tests ของสมการ
│   └── test_web.py             # Flask test client
├── requirements.txt
├── README.md
├── docs/
│   ├── superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md   # ไฟล์นี้
│   ├── design-note.md          # สรุปสถาปัตยกรรม + เหตุผลการตัดสินใจ (~1 หน้า)
│   ├── validation.md           # การคำนวณอ้างอิงด้วยมือ
│   └── reflection.md           # เขียนโดยนักศึกษา
├── .gitignore
└── .gitattributes
```

## 8. Contract ของ `dc_bias.py`

```python
def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> dict:
    """vcc,vbe [V]; r1,r2,rc,re [ohm]; beta [ dimensionless ]
    คืน dict; โยน ValueError(ข้อความภาษาไทย) เมื่ออินพุตผิดเงื่อนไข"""
```

**การตรวจอินพุต (โยน `ValueError`)**
- `vcc <= 0`, `r1 <= 0`, `r2 <= 0`, `rc <= 0`, `re <= 0`, `beta <= 0`
- ค่าที่ไม่ใช่ตัวเลข (ตรวจที่ `app.py` ก่อนเรียกฟังก์ชัน)
- `vbe` ต้อง `0 <= vbe < vcc`

**ผลลัพธ์ (หน่วย SI: V, A)**

```python
{
  "vth": float, "rth": float,          # V, ohm
  "ib": float, "ic": float, "ie": float,   # A
  "vb": float, "ve": float, "vc": float, "vce": float,  # V
  "ic_sat": float,                     # A = VCC/(RC+RE) — ขอบเขตอิ่มตัว คำนวณทุกครั้ง
  "region": "active" | "cutoff" | "saturation",
  "warnings": list[str],               # ว่างเมื่อ active
}
```

**สมการ (Forward-Active, β และ VBE คงที่)**

```
VTH = VCC·R2/(R1+R2)            RTH = R1·R2/(R1+R2)
IB  = (VTH − VBE)/(RTH + (β+1)·RE)
IC  = β·IB        IE = (β+1)·IB
VE  = IE·RE       VB = VE + VBE
VC  = VCC − IC·RC  VCE = VC − VE
```

**Region detection**

| เงื่อนไข | region | ค่าที่รายงาน | warnings |
|----------|--------|---------------|----------|
| `VTH <= VBE` | `cutoff` | clamp: `IB=IC=IE=0`, `VE=0`, `VB=VTH`, `VC=VCC`, `VCE=VCC` | "VTH (x.xx V) ≤ VBE (0.70 V): ทรานซิสเตอร์อยู่ในช่วง Cutoff ค่าที่แสดงเป็นการประมาณ" |
| `VCE <= 0` (จากสมการ) | `saturation` | รายงานค่าที่สมการให้มา **ตามจริง ไม่ clamp** (VC และ VCE อาจติดลบ) พร้อม `ic_sat` ใน dict | "VCE ที่คำนวณได้ ≤ 0 V: สมการ Forward-Active ใช้ไม่ได้ ทรานซิสเตอร์อิ่มตัว (IC(sat) ≈ x mA)" |
| อื่น ๆ | `active` | ตามสมการ | `[]` |

> เกณฑ์ saturation ยึดตามใบงาน (`VCE ≤ 0`) ไม่ใช้ VCE(sat) = 0.3 V

## 9. `app.py`

- `GET /` → render `index.html` พร้อมค่าเริ่มต้น = ค่าตัวอย่างในใบงาน (ยังไม่แสดงผลลัพธ์)
- `POST /` → parse ฟอร์ม → validate → เรียก `calculate_dc_bias` → render หน้าเดิมพร้อมผล
- **หน่วยตัวต้านทาน:** 4 dropdown `unit_r1..unit_re` ค่า `Ω` / `kΩ` (default `kΩ`) แปลงเป็น Ω ก่อนเรียกฟังก์ชัน
- **Validation ฝั่งเซิร์ฟเวอร์:** ฟิลด์ว่าง, แปลง float ไม่ได้, ค่าติดลบ/ศูนย์ → แสดง error ใต้ฟอร์ม
  - ตอบกลับด้วย **HTTP 200** พร้อม error (ไม่ใช้ 400) เพื่อให้หน้าเว็บยังแสดงฟอร์มและค่าที่กรอกไว้ ตาม A4
- เก็บค่าที่ผู้ใช้กรอกไว้ในฟอร์มหลังส่ง (sticky form)
- ไม่มี business logic ใน route: แปลงหน่วย → เรียกฟังก์ชัน → ส่ง dict เข้า template

## 10. `templates/index.html` + `static/style.css`

- ฟอร์ม 7 ช่อง (VCC, R1, R2, RC, RE, β, VBE) + 4 unit dropdown
- แผนผังวงจรแบบ inline SVG (Voltage-Divider + RC/RE + NPN) วาดเอง ~25 บรรทัด
- ตารางผลลัพธ์: VB, VE, VC, VCE [V] · IC [mA] · IB [µA] · IE [mA] · VTH [V] · RTH [kΩ]
  - แถว **IC(sat)** [mA] แสดงเพิ่มเฉพาะเมื่อ `region == "saturation"`
- กล่อง Warning (สีส้ม) และกล่อง Error (สีแดง) แสดงเฉพาะเมื่อมี
- ป้าย Region: Active / Cutoff / Saturation
- CSS: 2 คอลัมน์บนจอใหญ่, 1 คอลัมน์บนมือถือ
- ห้ามมีสมการหรือตัวเลขคำนวณในไฟล์นี้

## 11. Tests

**`tests/test_dc_bias.py`** (ค่าอ้างอิงจากข้อ 12, tolerance สัมพัทธ์ 1e-3)

1. `test_sample_bias_point` — ค่าตัวอย่าง → VTH, IB, IC, IE, VE, VB, VC, VCE ตรงตามอ้างอิง, region = active, warnings ว่าง
2. `test_cutoff_region` — R2 = 5 kΩ → region = cutoff, IC = 0, มี warning
3. `test_saturation_region` — RC = 15 kΩ → region = saturation, `ic_sat` ≈ 0.75 mA (tolerance 1e-3), VC ≈ −6.448 V, VCE ≈ −7.690 V, มี warning
4. `test_invalid_resistor_raises` — R ≤ 0 โยน ValueError
5. `test_invalid_beta_raises` — β ≤ 0 โยน ValueError

**`tests/test_web.py`**

6. `test_get_form` — `GET /` → 200 และมี `name="vcc"` ฯลฯ
7. `test_post_sample_values` — POST ค่าตัวอย่าง (หน่วย kΩ) → 200 และหน้าเว็บมี `8.052` (VCE)
8. `test_post_invalid_shows_error` — POST `r1=0` → 200, มีข้อความ error, ไม่มี traceback
9. `test_post_non_numeric` — POST `vcc=abc` → 200 + error

> รันด้วย `python -m unittest discover -s tests -v`

## 12. ค่าอ้างอิงสำหรับตรวจ (คำนวณมือ)

อินพุต: VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V

| ปริมาณ | ค่า |
|--------|-----|
| VTH | 2.1639 V |
| RTH | 18.0328 kΩ |
| IB | 12.299 µA |
| IC | 1.2299 mA |
| IE | 1.2422 mA |
| VE | 1.2422 V |
| VB | 1.9422 V |
| VC | 9.2943 V |
| VCE | 8.0522 V |
| Region | Active |

**กรณี Cutoff:** เปลี่ยน R2 = 5 kΩ → VTH = 0.571 V ≤ 0.70 V

**กรณี Saturation:** เปลี่ยน RC = 15 kΩ (ค่าอื่นเดิม) → IC = 1.2299 mA,
VC = 12 − 1.2299×15 = **−6.4479 V**, VE = 1.2422 V, **VCE = −7.6900 V** (≤ 0),
IC(sat) = 12/(15+1) = **0.7500 mA**

> หมายเหตุ: ค่า VCE ที่ติดลบเป็นผลจากสมการ Forward-Active ที่ถูกใช้เกินขอบเขต ไม่ใช่ค่าไฟฟ้าจริง
> หน้าเว็บต้องแสดงพร้อม Warning ไม่ใช่ซ่อนหรือ clamp

## 13. README ที่ต้องมี

1. ต้องมีอะไรในเครื่อง (Python 3.x)
2. สร้าง virtual environment + ติดตั้ง dependency
3. รันเว็บ + เปิด `http://127.0.0.1:5000/`
4. รัน tests
5. สมมติฐานของแบบจำลอง + ข้อจำกัด (Forward-Active, β คงที่, ไม่ใช่ SPICE)

## 14. Mapping กับเกณฑ์ตรวจรับ

| เกณฑ์ | ส่วนที่รองรับ |
|-------|----------------|
| A1 GET / | `app.py` + `index.html` |
| A2 POST คำนวณจริง | `calculate_dc_bias` |
| A3 ตรงกับการคำนวณอิสระ | ข้อ 12 + `docs/validation.md` |
| A4 Validation | ข้อ 9 + test 8, 9 |
| A5 Warning นอก Active | ข้อ 8 + test 2, 3 |
| A6 Unit + HTTP tests | ข้อ 11 |
| A7 Reproducibility | README ข้อ 13 |

## 15. สิ่งที่เหลือให้ผู้สร้างตัดสินใจ

- ถ้อยคำและระดับรายละเอียดของข้อความ error/warning
- การจัดวางหน้า, สี, ระยะห่าง, การออกแบบ SVG
- การปัดทศนิยมเพื่อแสดงผล (แนะนำ 3 ตำแหน่ง) — ค่าที่เก็บใน dict ไม่ปัด
- รายละเอียดโครงสร้าง test เพิ่มเติมที่ไม่ขัดกับข้อ 11
- เนื้อหา `docs/reflection.md` (นักศึกษาเขียนเอง)

## 16. การตัดสินใจที่ปิดหลัง Builder Check

1. **VC vs VCE ในกรณี Saturation** — แก้ตัวเลขในข้อ 12 ให้ถูก: `VC = −6.4479 V` และ
   `VCE = VC − VE = −7.6900 V` (ฉบับก่อนหน้าอ้าง −6.45 V เป็น VCE ซึ่งผิด) ค่าที่แสดง
   ต้องไม่ถูก clamp และต้องมี Warning กำกับ
2. **`ic_sat`** — เป็นคีย์ใน dict เสมอ (คำนวณทุกครั้ง) ไม่ใช่แค่ข้อความใน warning
   และ template แสดงแถว IC(sat) เฉพาะเมื่อ `region == "saturation"`
3. **`docs/design-note.md`** — เป็นเอกสารสรุปสถาปัตยกรรม 1 หน้า เขียนโดยผู้สร้าง
   (ภาพรวมการแยกไฟล์, contract ของ `dc_bias.py`, เหตุผลที่เลือกทาง A) ไม่ใช่รายงานคะแนน

