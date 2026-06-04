import os
import subprocess
import time
import shlex

# ⚙️ ตั้งค่าพิกัดคลังเพลงของคุณที่มีปัญหาไฟล์ค้าง
TARGET_REPO = r'C:\MyLibrary\7_Music' 

def run_git(command, cwd):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=300)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, "", str(e)

print("🚀 [เริ่มระบบเคลียร์คิว LFS แบบปลอดภัย]")
if not os.path.exists(os.path.join(TARGET_REPO, ".git")):
    print("❌ ไม่พบโฟลเดอร์ .git ในพิกัดที่ระบุ กรุณาตรวจสอบพิกัด TARGET_REPO")
    exit()

# 1. ค้นหาโฟลเดอร์ย่อยที่มีไฟล์เพลงอยู่ข้างใน
subfolders = []
for root, dirs, files in os.walk(TARGET_REPO):
    # กรองเฉพาะโฟลเดอร์ที่มีไฟล์เพลง .mp3 อยู่จริง
    if any(f.lower().endswith('.mp3') for f in files):
        rel_path = os.path.relpath(root, TARGET_REPO)
        subfolders.append(rel_path)

print(f"📦 ตรวจพบกลุ่มโฟลเดอร์ที่ต้องทยอยอัปโหลดทั้งหมด {len(subfolders)} กลุ่ม")

# 2. เริ่มกระบวนการทยอยส่งทีละโฟลเดอร์เพื่อความปลอดภัย
for idx, folder in enumerate(subfolders, 1):
    print(f"\n🔄 [{idx}/{len(subfolders)}] กำลังจัดการโฟลเดอร์: {folder if folder != '.' else 'โฟลเดอร์หลัก'}")
    
    # ดักจับชื่อโฟลเดอร์สำหรับใช้ในคำสั่ง Git
    search_path = "*" if folder == "." else f"{folder}/*"
    
    # สั่ง Add เฉพาะกลุ่มไฟล์ในโฟลเดอร์นี้
    run_git(f'git add {shlex.quote(search_path)}', TARGET_REPO)
    
    # สั่ง Commit
    run_git(f'git commit -m "Safe sync clear queue part {idx}"', TARGET_REPO)
    
    # สั่ง Push เฉพาะเนื้อหา LFS ของกลุ่มนี้ขึ้นไปก่อน
    print(f" 📤 กำลัง Push เนื้อหาไฟล์สื่อ (LFS)...")
    lfs_code, _, lfs_err = run_git(f'git lfs push origin main', TARGET_REPO) # หรือเปลี่ยนเป็น master ถ้าคลังใช้ชื่อนั้น
    
    # สั่ง Push Pointer อัปเดตสถานะของกลุ่มนี้
    print(f" ☁️ กำลังอัปเดตโครงสร้างบน GitHub...")
    code, _, err = run_git("git push origin HEAD", TARGET_REPO)
    
    if code == 0:
        print(f" ✅ โฟลเดอร์ที่ {idx} ส่งขึ้น GitHub สำเร็จแล้ว!")
    else:
        print(f" ❌ เกิดข้อผิดพลาดชั่วคราว: {err if err else lfs_err}")
    
    # หน่วงเวลา 5 วินาที เพื่อให้เซิร์ฟเวอร์ GitHub ได้พักและเคลียร์ทราฟฟิก
    print(" 💤 พักระบบ 5 วินาทีเพื่อความปลอดภัย...")
    time.sleep(5)

print("\n🎉 [เสร็จสิ้น] สคริปต์ได้กวาดและทยอยส่งไฟล์เพลงที่ค้างอยู่ทั้งหมดขึ้น GitHub เรียบร้อยแล้วครับ!")