# SLE - Stellaris Localisation Editor

**โปรแกรมแก้ไขคำแปลภาษาไทยสำหรับเกม Stellaris**

---

## Download

| Version | Download | Note |
|---------|----------|------|
| **v1.0.0** | [SLE-v1.0.0-windows.zip](https://github.com/zLemonKungz/Stellaris-Localisation-Editor/releases/latest) | Windows 64-bit, portable (ไม่ต้องติดตั้ง) |

**วิธีใช้:**
1. ดาวน์โหลด `SLE-v1.0.0-windows.zip`
2. แตก zip
3. เปิด `SLE.exe`
4. กด `Ctrl+O` → เลือกโฟลเดอร์ `localisation/` ของมอด Stellaris
5. เริ่มแก้ไขคำแปล

> ต้องการใช้จาก source code? ดูหัวข้อ **Run from Source** ด้านล่าง

---

## Features

- แก้ไขไฟล์คำแปล `.yml` ทั้งหมดในมอด
- ตรวจสอบสถานะคำแปล Real-time (ตรวจจับภาษาไทยจริง)
- AI Translate รองรับ NVIDIA, Gemini, Claude, Ollama
- Spell Check ไทย + อังกฤษ
- Glossary คำศัพท์ Stellaris
- Dark Theme
- Package for Translation / Apply Translation Package

## Requirements (from source)

- Python 3.12+
- PyQt6
- requests

## Run from Source

```bash
git clone https://github.com/zLemonKungz/Stellaris-Localisation-Editor.git
cd Stellaris-Localisation-Editor
pip install -r requirements.txt
python localisation_editor/main.py
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+O | Open mod folder |
| Ctrl+S | Save current file |
| Ctrl+Shift+T | AI Translate |
| Ctrl+F | Find in file |
| Ctrl+Shift+F | Global Search |
| Ctrl+1-4 | Switch tabs |
| Ctrl+E | Focus editor |
| Ctrl+Q | Exit |

## License

MIT License

Copyright (c) 2026 Lemon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
