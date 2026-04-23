import os
import subprocess
import time

# --- ตั้งค่าตำแหน่งห้องต่างๆ ---
repositories = [
    r'C:\MyWebProjectsmybook',
    r'C:\MyLibrary\1_PetchPraUma',
    r'C:\MyLibrary\2_Thai_Novel',
    r'C:\MyLibrary\3_English_Translated',
    r'C:\MyLibrary\4_Chinese_Novel',
    r'C:\MyLibrary\5_HowTo_Religion',
    r'C:\MyLibrary\6_HowTo_Religion_Science'
]

BATCH_SIZE = 30  # ส่งทีละ 30 ไฟล์เพื่อให้เสถียรสำหรับไฟล์ PDF

def optimize_git():
    """ตั้งค่า Git ให้รองรับไฟล์ใหญ่"""
    subprocess.run(['git', 'config', 'http.postBuffer', '524288000'], shell=True)

def run_local_scripts():
    print("\n--- 🛠️ STEP 1: เตรียมข้อมูลเฉพาะส่วนที่เพิ่มใหม่ ---")
    # ลำดับ: สร้าง DB -> ดึงรูปปกเฉพาะเล่มที่ยังไม่มี -> ทำความสะอาด
    scripts = ['gen_db.py', 'extract_covers.py', 'clean_db.py']
    for script in scripts:
        if os.path.exists(script):
            print(f"🚀 กำลังรัน: {script}")
            subprocess.run(f"python {script}", shell=True)
        else:
            print(f"⚠️ ไม่พบไฟล์: {script}")

def auto_push_loop(repo_path):
    if not os.path.exists(os.path.join(repo_path, '.git')):
        return

    os.chdir(repo_path)
    optimize_git()
    repo_name = os.path.basename(repo_path)
    
    print(f"\n--- 📤 STEP 2: ทยอยส่งไฟล์ขึ้น GitHub (เฉพาะส่วนที่เปลี่ยน) ---")
    print(f"📍 ห้อง: {repo_name}")

    # --- จุดแก้ไขสำคัญ: สั่ง Add เฉพาะไฟล์ที่จำเป็นเท่านั้น ---
    print("📋 กำลังบันทึกการเปลี่ยนแปลง (database และ covers)...")
    subprocess.run(['git', 'add', 'database.json'], shell=True)
    subprocess.run(['git', 'add', 'covers/*'], shell=True)

    while True:
        # ตรวจสอบไฟล์ที่ Add ค้างไว้ (Staged)
        result = subprocess.run(['git', 'diff', '--name-only', '--cached'], 
                                capture_output=True, text=True, shell=True)
        files = result.stdout.splitlines()

        if not files:
            print(f"✨ {repo_name} อัปเดตเสร็จสมบูรณ์!")
            break

        current_batch = files[:BATCH_SIZE]
        print(f"📦 กำลังแพ็กและส่ง {len(current_batch)} ไฟล์... (เหลือค้างอีก {len(files)})")

        # Commit เฉพาะไฟล์ในกลุ่มนี้
        msg = f"Auto-sync {time.strftime('%Y-%m-%d %H:%M')} ({len(current_batch)} files)"
        subprocess.run(['git', 'commit', '-m', msg] + current_batch, shell=True)

        # Push ขึ้น GitHub
        print("🚀 กำลังส่งขึ้นเซิร์ฟเวอร์...")
        push_status = subprocess.run(['git', 'push'], shell=True)

        if push_status.returncode != 0:
            print("⚠️ ติดขัดชั่วคราว จะลองใหม่ใน 15 วินาที...")
            time.sleep(15)
        else:
            print("✅ ส่งรอบนี้สำเร็จ พักเครื่อง 3 วินาที...")
            time.sleep(3)

def main():
    start_time = time.time()
    
    # 1. จัดการข้อมูลในเครื่องให้เสร็จก่อน
    run_local_scripts()
    
    # 2. วนลูปส่งของขึ้น GitHub
    initial_dir = r'C:\MyWebProjectsmybook'
    for repo in repositories:
        auto_push_loop(repo)
        os.chdir(initial_dir)

    duration = round(time.time() - start_time, 2)
    print(f"\n================================================")
    print(f"✅ ทุกอย่างเสร็จสมบูรณ์ใน {duration} วินาที!")
    print(f"พัดลมคอมพิวเตอร์ของคุณควรจะเบาลงแล้วครับ 😊")
    print(f"================================================")

if __name__ == "__main__":
    main()