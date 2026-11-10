# BJT DC Bias Web App — ENG29 2121 Lab 02

เว็บแอปพลิเคชันคำนวณ **DC Operating Point** ของวงจรขยาย BJT NPN
แบบ Common-Emitter Voltage-Divider Bias โดยรับค่าอุปกรณ์จากหน้าเว็บ
แล้วให้ **Python Backend** คำนวณด้วยสมการ Forward-Active
ผลลัพธ์แสดงเป็นตารางพร้อมหน่วย ผ่าน Flask Server ที่ `http://127.0.0.1:5000/`

## โครงสร้างโปรเจกต์

```
.
├── app.py                  # Flask routes, แปลงหน่วย, รวม error
├── dc_bias.py              # สมการ DC Bias (ไม่รู้จัก HTML/HTTP)
├── templates/index.html    # ฟอร์ม + ผลลัพธ์ (Jinja2)
├── static/style.css        # หน้าตาเว็บ
├── tests/
│   ├── test_dc_bias.py     # 9 unit tests ของสมการ
│   └── test_web.py         # 14 HTTP tests ผ่าน Flask test client
├── requirements.txt
├── docs/
│   ├── design-note.md      # สถาปัตยกรรมและเหตุผลการตัดสินใจ
│   ├── validation.md       # เทียบค่าคำนวณมือกับผลโปรแกรม
│   └── reflection.md       # สิ่งที่ได้เรียนรู้
└── .gitignore
```

## สิ่งที่ต้องมีในเครื่อง

- Python 3.10 ขึ้นไป (พัฒนาบน Python 3.14.2)
- ไม่ต้องติดตั้ง Node.js หรือ build tool ใด ๆ

## 1. ติดตั้ง

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> macOS / Linux: `python3 -m venv .venv` แล้ว `./.venv/bin/python -m pip install -r requirements.txt`

## 2. รันเว็บ

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000/>

> Flask debug server ใช้สำหรับเครื่องพัฒนาของตนเองเท่านั้น ห้ามเปิดให้เครือข่ายภายนอกเข้าถึง

## 3. รันทดสอบ

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ผลที่คาดหมาย: **23 tests OK** (9 tests ของสมการ + 14 tests ของ HTTP)

## 4. ค่าตัวอย่าง

| พารามิเตอร์ | ค่า |
|---|---|
| VCC | 12 V |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| RC | 2.2 kΩ |
| RE | 1 kΩ |
| β | 100 |
| VBE | 0.70 V |

ผลที่ควรได้: VB ≈ 1.942 V, VE ≈ 1.242 V, VC ≈ 9.294 V, VCE ≈ 8.052 V, IC ≈ 1.230 mA

## 5. สมมติฐานและข้อจำกัด

- ใช้ **Forward-Active Approximation**: β คงที่, VBE คงที่ (ไม่คิดอุณหภูมิ, Early effect, self-heating)
- ไม่ใช่การจำลอง SPICE และไม่มี AC / Transient analysis
- ค่าที่อยู่นอก Active Region (Cutoff / Saturation) จะแสดง **Warning** และไม่ควรนำไปใช้โดยไม่ตรวจสอบ
- เมื่อ VCE ≤ 0 โปรแกรมรายงานค่าตามสมการตามจริง (อาจติดลบ) พร้อม Warning แทนการปรับค่าให้ดูสมเหตุสมผล

## เอกสารเพิ่มเติม

- [`docs/design-note.md`](docs/design-note.md) — เหตุผลการแยกไฟล์และการตัดสินใจ
- [`docs/validation.md`](docs/validation.md) — การคำนวณมือเทียบกับผลโปรแกรม
