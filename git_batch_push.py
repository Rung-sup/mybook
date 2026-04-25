import subprocess
import time
import os

def run_git(command, cwd):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error: {e}")
        return None

def push_music_batches(batch_size=10):
    # กำหนดตำแหน่งที่ตั้งของ Library คุณ
    target_path = r"C:\MyLibrary"
    
    if not os.path.exists(target_path):
        print(f"❌ ไม่พบโฟลเดอร์ {target_path} กรุณาเช็กชื่อโฟลเดอร์อีกครั้งครับ")
        return

    print(f"📍 กำลังทำงานที่: {target_path}")

    # 1. กวาดไฟล์ทั้งหมดใน MyLibrary (รวมถึง 7_music_Vol2)
    print("📂 กำลังสแกนหาไฟล์ใหม่และไฟล์ที่เปลี่ยนแปลง...")
    run_git("git add .", target_path)
    
    # 2. ดึงรายชื่อไฟล์ที่รอ Push
    status = run_git("git diff --name-only --cached", target_path)
    
    if not status:
        print("✅ ไม่พบไฟล์ที่ต้องดำเนินการ (อาจจะ Push ไปหมดแล้ว หรือ Path ไม่ใช่ Git Repo)")
        return

    files = status.split('\n')
    total_files = len(files)
    print(f"📦 พบไฟล์ในคิวทั้งหมด: {total_files} ไฟล์")

    # 3. ถอยกลับมาเพื่อทยอย Push ทีละกลุ่ม
    run_git("git reset", target_path)

    # 4. เริ่ม Loop ทยอยส่ง
    for i in range(0, total_files, batch_size):
        batch = files[i:i + batch_size]
        print(f"\n🚀 [กลุ่มที่ {i//batch_size + 1}] กำลังจัดการไฟล์ที่ {i+1} ถึง {min(i+batch_size, total_files)}...")
        
        for file in batch:
            run_git(f'git add "{file}"', target_path)
        
        commit_msg = f"Sync Music Vol2 - Batch {i//batch_size + 1}"
        run_git(f'git commit -m "{commit_msg}"', target_path)
        
        print(f"📤 กำลัง Push ขึ้น GitHub...")
        run_git("git push", target_path)
        print(f"✅ สำเร็จ!")
        
        time.sleep(1) # ป้องกัน Server ตัดการเชื่อมต่อ

if __name__ == "__main__":
    push_music_batches(10)