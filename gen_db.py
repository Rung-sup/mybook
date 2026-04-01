import os
import json
import urllib.parse

base_dir = r"C:\MyLibrary"
github_username = "rung-sup"
repo_name = "mybook"

folders = [
    "1_PetchPraUma",
    "2_Thai_Novel",
    "3_English_Translated",
    "4_Chinese_Novel",
    "5_HowTo_Religion",
    "6_HowTo_Religion_Science"
]

all_books = []
total_count = 0

print(f"🔍 กำลังเริ่มสำรวจหนังสือใน {base_dir} ...\n")

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    folder_count = 0

    if not os.path.exists(folder_path):
        print(f"⚠️ ข้าม: หาโฟลเดอร์ไม่พบ -> {folder_path}")
        continue

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.pdf', '.epub')):
                title = os.path.splitext(file)[0]

                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                rel_path_web = rel_path.replace("\\", "/")

                parts = rel_path_web.split('/')
                encoded_parts = [urllib.parse.quote(p) for p in parts]
                final_path = "/".join(encoded_parts)

                full_url = f"https://{github_username}.github.io/{repo_name}/{folder}/{final_path}"

                book_data = {
                    "title": title,
                    "url": full_url
                }

                all_books.append(book_data)
                folder_count += 1
                total_count += 1

    print(f"✅ โกดัง [{folder}]: กวาดมาได้ {folder_count} เล่ม")

output_file = "database.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"🎉 สำเร็จ! สร้างไฟล์ {output_file} อัปเดตล่าสุดแล้ว")
print(f"📚 ยอดรวมหนังสือทั้งหมดจากทุกโกดัง: {total_count} เล่ม")