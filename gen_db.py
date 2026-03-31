import os
import json

# 1. ที่อยู่โฟลเดอร์หลักในเครื่อง (ที่มีโฟลเดอร์ย่อยข้างใน)
book_folder = r'C:\MyLibrary\2_Thai_Novel'

# 2. URL หน้าบ้านบน GitHub
base_url = 'https://rung-sup.github.io/2_Thai_Novel/' 

books = []

# 3. ใช้ os.walk เพื่อมุดเข้าไปหาไฟล์ในทุกโฟลเดอร์ย่อย
for root, dirs, files in os.walk(book_folder):
    for filename in files:
        # เช็คว่าเป็นไฟล์ PDF (รองรับทั้งตัวเล็ก .pdf และตัวใหญ่ .PDF)
        if filename.lower().endswith('.pdf'):
            
            # หาที่อยู่สัมพัทธ์ (Relative Path) เพื่อทำลิงก์ให้ถูกต้องตามโครงสร้างโฟลเดอร์
            relative_path = os.path.relpath(os.path.join(root, filename), book_folder)
            # เปลี่ยนเครื่องหมาย \ เป็น / เพื่อให้ลิงก์เว็บใช้งานได้
            web_path = relative_path.replace('\\', '/')
            
            book_data = {
                "title": filename.replace('.pdf', '').replace('.PDF', ''),
                "url": base_url + web_path,
                "category": "นิยายไทย"
            }
            books.append(book_data)

# 4. บันทึกลงใน database.json
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=4)

print(f"สำเร็จ! กวาดรายชื่อหนังสือจากทุกโฟลเดอร์ย่อยได้ทั้งหมด {len(books)} เล่มเรียบร้อยครับ")