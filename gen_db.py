import os
import json

# สคริปต์เวอร์ชัน "ค้นหาอัตโนมัติ" - ไม่ต้องระบุชื่อโฟลเดอร์เป๊ะๆ
db_data = {}

# รายชื่อหมวดหมู่หลักที่คุณต้องการให้โชว์บนหน้าเว็บ (เอาแค่หัวข้อหลัก)
main_categories = [
    "1_PetchPraUma",
    "2_Thai_Novel",
    "3_English_Translated",
    "4_Chinese_Novel",
    "5_HowTo_Religion",
    "5_HowTo_Religion_Science"
]

def scan_files(target_path):
    """กวาดไฟล์ PDF/EPUB ทั้งหมดในโฟลเดอร์ที่กำหนด (รวมโฟลเดอร์ย่อย)"""
    found_files = []
    for root, dirs, files in os.walk(target_path):
        for file in files:
            if file.lower().endswith(('.pdf', '.epub')):
                found_files.append(file.strip())
    return sorted(list(set(found_files)))

# เริ่มต้นการกวาดข้อมูล
print("🚀 เริ่มต้นการกวาดข้อมูลหนังสือทั้งหมด...")

# หาตำแหน่งโฟลเดอร์หลัก (เช็คทั้งข้างนอก และใน mybook/)
base_paths = [".", "mybook"]

for cat_name in main_categories:
    found_path = None
    for bp in base_paths:
        test_path = os.path.join(bp, cat_name)
        if os.path.exists(test_path):
            found_path = test_path
            break
    
    if not found_path:
        print(f"⚠️ ไม่พบหมวด: {cat_name} (ข้าม)")
        db_data[cat_name] = []
        continue

    print(f"📂 กำลังนับสต็อกใน: {found_path}...")
    
    # ดูว่าข้างในมีโฟลเดอร์ย่อย (เช่น ttt ล่องไพร) ไหม
    subfolders = [d for d in os.listdir(found_path) if os.path.isdir(os.path.join(found_path, d))]
    
    if not subfolders:
        # ถ้าไม่มีโฟลเดอร์ย่อย (เหมือนเพชรพระอุมา)
        db_data[cat_name] = scan_files(found_path)
    else:
        # ถ้ามีโฟลเดอร์ย่อย (เช่น นิยายไทยที่มี ttt นำหน้า)
        cat_dict = {}
        for sub in subfolders:
            sub_path = os.path.join(found_path, sub)
            files = scan_files(sub_path)
            if files:
                cat_dict[sub.strip()] = files
        
        # เก็บไฟล์ที่หลุดอยู่นอกโฟลเดอร์ย่อย
        root_files = [f for f in os.listdir(found_path) if os.path.isfile(os.path.join(found_path, f)) and f.lower().endswith(('.pdf', '.epub'))]
        if root_files:
            cat_dict["Other_Files"] = sorted(list(set(root_files)))
            
        db_data[cat_name] = cat_dict

# บันทึกไฟล์
try:
    with open('database.json', 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=4)
    print("\n✅ สำเร็จ! ตอนนี้เปิด database.json แล้วหาคำว่า 'ล่องไพร' ได้เลยครับ!")
except Exception as e:
    print(f"\n❌ ข้อผิดพลาด: {e}")