# SLE - Stellaris Localisation Editor

**โปรแกรมแก้ไขคำแปลภาษาไทยสำหรับเกม Stellaris**

---

## เกี่ยวกับโปรแกรม

SLE (Stellaris Localisation Editor) เป็นโปรแกรม Desktop GUI สำหรับแก้ไขไฟล์คำแปล `.yml` ของเกม Stellaris โดยเฉพาะ รองรับการตรวจสอบความถูกต้องของคำแปลภาษาไทยแบบ Real-time มีระบบ AI ช่วยแปล และระบบตรวจคำผิด

## Features

- แก้ไขไฟล์คำแปล `.yml` ทั้งหมดในมอด
- ตรวจสอบสถานะคำแปลแบบ Real-time (ตรวจจับภาษาไทยจริง ไม่ใช่แค่เช็คว่ามีค่าหรือไม่)
- AI Translate รองรับ NVIDIA, Gemini, Claude API และ Ollama (Local)
- ระบบตรวจคำผิด (Spell Check) รองรับทั้งไทยและอังกฤษ
- Glossary อ้างอิงคำศัพท์ Stellaris
- รองรับหลายมอด - เปลี่ยนโฟลเดอร์มอดได้ (File > Open Mod Folder)
- Dark Theme
- รองรับการทำงานร่วมกัน: Package for Translation + Apply Translation Package

## Requirements

- Python 3.12+
- PyQt6
- requests

## Quick Start

```bash
pip install -r requirements.txt
cd localisation_editor && python main.py
```

## วิธีเริ่มใช้งาน

1. เปิดโปรแกรม → `File > Open Mod Folder...` (Ctrl+O)
2. เลือกโฟลเดอร์ `localisation/` ของมอด Stellaris
3. เริ่มแก้ไขคำแปลในหน้า Editor
4. กด `Ctrl+S` เพื่อบันทึก

## Features

| ปุ่ม/เมนู | คำอธิบาย |
|-----------|----------|
| Editor (Ctrl+1) | เรียกดูและแก้ไขไฟล์คำแปล พร้อมระบบค้นหา |
| Overview (Ctrl+D) | ดูสถิติคำแปล Real-time |
| Search (Ctrl+Shift+F) | ค้นหาทุกไฟล์ |
| Glossary | ดูคำศัพท์ Stellaris |
| File > AI Translate (Ctrl+Shift+T) | แปลด้วย AI อัตโนมัติ |
| File > Package for Translation | ส่งออกเฉพาะ key ที่ยังไม่ได้แปล |
| File > Apply Translation Package | นำเข้าคำแปลที่ได้กลับมา |

## License

MIT
