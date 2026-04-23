import os

categories = ["1_PetchPraUma", "2_Thai_Novel", "3_English_Translated", "4_Chinese_Novel", "5_HowTo_Religion_Science"]

for cat in categories:
    if not os.path.exists(cat): continue
    
    # วนลูปทุกไฟล์และโฟลเดอร์ (รวมลูกข่าย)
    for root, dirs, files in os.walk(cat):
        for name in files:
            if name.startswith(" ") or name.endswith(" "):
                old_path = os.path.join(root, name)
                new_name = name.strip()
                new_path = os.path.join(root, new_name)
                print(f"กำลังเปลี่ยนชื่อ: '{name}' -> '{new_name}'")
                os.rename(old_path, new_path)

print("เปลี่ยนชื่อไฟล์ที่มีช่องว่างในเครื่องเรียบร้อยแล้ว!")