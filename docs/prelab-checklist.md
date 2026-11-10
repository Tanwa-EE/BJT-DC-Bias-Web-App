# Checklist ก่อนเริ่มทำงานจริง — ENG29 2121 Lab 02

> ตรวจเมื่อ: 10 พ.ย. 2569 · เครื่อง: `C:\Users\569187`
> เกณฑ์อ้างอิง: ใบงาน Lab 02 หัวข้อ 2.1–2.4

## ผลตรวจ (หลักฐานจากการรันจริง)

| # | รายการ | คำสั่ง / วิธีตรวจ | ผลที่ได้ | สถานะ |
|---|--------|------------------|----------|--------|
| 1 | Git ติดตั้งแล้ว | `git --version` | `git version 2.56.0.windows.4` | ✅ |
| 2 | Git ตั้งชื่อผู้ออก commit | `git config --global --get user.name` | `Tanwa` | ✅ |
| 3 | Git ตั้งอีเมลผู้ออก commit | `git config --global --get user.email` | `tanwa.tu@g.sut.ac.th` | ✅ |
| 4 | Git Credential Manager | `git config --system --get credential.helper` | `manager` | ✅ |
| 5 | GitHub Desktop ติดตั้งแล้ว | About ในแอป | `3.6.10` | ✅ |
| 6 | บัญชี GitHub เชื่อมแล้ว | Windows Credential Manager | `GitHub - https://api.github.com/Tanwa-EE` | ✅ |
| 7 | Repository เปิดได้ | GitHub Desktop → Current Repository | `BJT DC Bias Web App` (branch `main`, commit `8db086e`) | ✅ |
| 8 | Remote ของ Repository | `git remote -v` | *ยังว่าง — ต้องกด Publish ใน GitHub Desktop* | ⏳ |
| 9 | OpenCode Desktop | About / `opencode --version` | `2.2.6` (V2) | ✅ |
| 10 | Superpowers Plugin | `opencode plugin list` | `superpowers  22f0b46` | ✅ |
| 11 | Superpowers โหลดจริงในแอป | `GET /api/plugin` | `"status": "active"` | ✅ |
| 12 | Skill ครบ | นับ `SKILL.md` ในแพ็กเกจ | 15 skills (brainstorming, writing-plans, executing-plans, …) | ✅ |
| 13 | Python | `python --version` | `Python 3.14.2` | ✅ |
| 14 | pip | `python -m pip --version` | `pip 25.3` | ✅ |
| 15 | Flask | `python -c "import flask"` | ยังไม่ติดตั้ง (จะติดตั้งใน `.venv`) | ⏳ |

## สิ่งที่แก้ไประหว่างตรวจ

1. **ติดตั้ง Git** — เครื่องยังไม่มี Git ทำให้ Plugin ติดตั้งไม่ผ่าน (`An unknown git error occurred`)
2. **เพิ่ม Python ลง PATH** — เดิม `python` ชี้ไปที่ Microsoft Store stub (`WindowsApps\python.exe`) และรันไม่ทำงาน
   เพิ่ม `C:\Program Files\Python314` และ `...\Scripts` ไว้หน้าสุดของ User PATH
   → ย้อนกลับได้โดยลบสองรายการนั้นออกจาก Environment Variables
3. **ยังต้องทำ:** ปิด–เปิด OpenCode Desktop 1 ครั้ง เพื่อให้ process ของแอปได้รับ PATH ใหม่ (ถ้าไม่ทำ คำสั่ง `git` ใน Tool shell จะยังขึ้น "not recognized")

## ขั้นตอน Commit ด้วย GitHub Desktop

1. เปิด GitHub Desktop → **Current Repository** = `BJT DC Bias Web App`
2. แท็บ **Changes** ด้านซ้าย → ติ๊กเลือกไฟล์ที่จะ commit (ตรวจว่าไม่มี `.venv/`, `.env`, API key)
3. ช่อง **Summary** พิมพ์ข้อความสั้น ๆ เช่น `chore: add pre-lab checklist` (ช่อง Description เว้นได้)
4. กด **Commit to main**
5. ครั้งแรกที่ยังไม่มี remote → กด **Publish repository**
   - ติ๊ก **Keep this code private** ถ้าเป็นงานส่วนตัว
   - ห้ามติ๊ก **Initialize with README** (repo มี commit อยู่แล้ว)
6. ตรวจว่า Push สำเร็จ → แท็บ **History** ต้องไม่ขึ้น "Push origin" ค้าง
7. คัดลอก **URL ของ repo บน GitHub** + **Commit SHA** (คลิกขวาที่ commit → Copy SHA) ไปส่งใน Moodle

## กติกาก่อน commit ทุกครั้ง

- ตรวจ `git status` ว่าไม่มีไฟล์เกินที่ตั้งใจ
- ห้าม commit `.venv/`, `__pycache__/`, `.env`, API key, token
- ข้อความ commit ควรบอกว่า "ทำอะไร" (เช่น `feat: add DC bias calculation module`)
