# Design Note — BJT DC Bias Web App

## ภาพรวม

เว็บแอปพลิเคชันนี้แยกความรับผิดชอบออกเป็น 5 ส่วน เพื่อให้เห็นว่า Web Application
ไม่ใช่ไฟล์ HTML ไฟล์เดียว แต่ประกอบจาก Frontend, HTTP Routing, Backend Logic,
Static Resource และ Automated Tests

| ไฟล์ | รับผิดชอบ | ห้ามทำ |
|------|-----------|--------|
| `dc_bias.py` | สมการ DC Bias, validation, ตรวจ region | ห้าม import Flask, ห้ามรู้จัก HTML |
| `app.py` | รับ HTTP, แปลงหน่วย, รวม error, เรียกฟังก์ชัน | ห้ามมีสมการฟิสิกส์ |
| `templates/index.html` | แสดงฟอร์มและผลลัพธ์ | ห้ามคำนวณหรือเก็บสมการ |
| `static/style.css` | หน้าตาและการจัดวาง | — |
| `tests/` | พิสูจน์ทั้งสมการและ HTTP | — |

## Contract ของ `dc_bias.py`

```python
calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> dict
```

- รับหน่วย SI: V, Ω, A (β ไม่มีหน่วย)
- โยน `ValueError` พร้อมข้อความภาษาไทยเมื่ออินพุตผิดเงื่อนไข
- คืน dict: `vth`, `rth`, `ib`, `ic`, `ie`, `vb`, `ve`, `vc`, `vce`, `ic_sat`, `region`, `warnings`

การแปลง kΩ → Ω เกิดใน `app.py` เท่านั้น ทำให้ `dc_bias.py` ไม่ต้องรู้ว่าผู้ใช้กรอกหน่วยอะไร

## ทำไมเลือก route เดียว (GET + POST ที่ `/`)

พิจารณา 3 ทาง:

1. **route เดียว + Jinja** (เลือก) — โค้ดน้อย ทดสอบด้วย Flask test client ได้ตรงไปตรงมา
2. JSON API + fetch — UX ลื่นกว่า แต่ต้องจัดการ error สองชั้น และ test ครอบคลุมได้น้อยลง
3. POST → redirect (PRG) — HTTP ถูกต้องที่สุด แต่ต้องเก็บ state เพิ่ม เกินขอบเขตของ Lab 2

ข้อจำกัดที่ยอมรับ: กด refresh หลัง POST จะถูกถามยืนยันการส่งฟอร์มซ้ำ ซึ่งยอมรับได้ในระดับ Lab

## การตัดสินใจสำคัญ

- **Validation ฝั่งเซิร์ฟเวอร์เสมอ** — ไม่พึ่ง `type="number"` ของเบราว์เซอร์ เพราะผู้ใช้สามารถปิดได้
- **ปฏิเสธ `nan` / `inf`** — `float()` ของ Python ยอมรับทั้งสองค่า ทำให้ผลลัพธ์เพี้ยนโดยไม่มีการเตือน
- **Region cutoff** — clamp กระแสเป็นศูนย์ เพราะสมการให้ค่า IB ติดลบซึ่งไม่มีความหมายทางกายภาพ
- **Region saturation** — ไม่ clamp ค่าที่สมการให้มา แต่ติด Warning เพราะต้องการให้เห็นว่าแบบจำลองหลุดขอบเขต
- **เก็บค่าดิบของฟอร์มไว้** — เมื่อเกิด error ผู้ใช้ไม่ต้องพิมพ์ใหม่ทั้งหน้า

## สิ่งที่จงใจไม่ทำใน Lab นี้

AC small-signal, Bode plot, Transient, Bias แบบอื่น (Fixed/Emitter), SPICE/ngspice,
Interactive schematic และระบบ deploy ขึ้นเซิร์ฟเวอร์สาธารณะ — ทั้งหมดอยู่ในแผนรายวิชาสัปดาห์ถัดไป

## ข้อจำกัดของแบบจำลอง

แบบจำลองนี้เป็น Forward-Active Approximation ที่ถือว่า β และ VBE คงที่
ไม่คำนวณ temperature effect, Early effect หรือ self-heating
ผลลัพธ์จึงใช้เพื่อการเรียนรู้โครงสร้าง Web App ไม่ใช่แทนการจำลอง SPICE
