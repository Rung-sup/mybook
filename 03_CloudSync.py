import os
import subprocess
import time

# ==========================================
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'
# ==========================================

def run_git(command, cwd):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=60)
        return result.stdout.strip()
    except: return None

def main():
    print("☁️ [3/3] กำลังเช็กความเปลี่ยนแปลงและส่งข้อมูลขึ้น Cloud...")
    
    # ส่งโฟลเดอร์หนังสือ (ประหยัดเวลาโดยเช็กสถานะก่อน)
    for folder in os.listdir(LIBRARY_ROOT):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.exists(os.path.join(f_p, ".git")):
            
            # เช็กว่ามีอะไรเปลี่ยนไหม ถ้าไม่มีให้ข้ามการส่งไปเลย
            status = run_git("git status --porcelain", f_p)
            if status:
                print(f"🚀 ตรวจพบการเปลี่ยนแปลง กำลังส่งห้อง: {folder}")
                run_git("git add .", f_p)
                run_git('git commit -m "Auto-sync update"', f_p)
                try:
                    subprocess.run("git push origin HEAD -f", cwd=f_p, shell=True, timeout=300)
                except: print(f"   ⚠️ {folder} Timeout")
            else:
                print(f"   ⏩ ข้ามห้อง {folder} (ไม่มีการเปลี่ยนแปลง)")

    # ส่งโฟลเดอร์ฐานข้อมูลหลัก (ส่งเสมอเพื่อให้แอปอัปเดต)
    if os.path.exists(os.path.join(DB_DIR, ".git")):
        print("\n💾 กำลังส่งฐานข้อมูลและปก (DB_DIR)...")
        run_git("git add .", DB_DIR)
        if run_git("git status --porcelain", DB_DIR):
            run_git('git commit -m "Update Audiobook DB"', DB_DIR)
            try:
                subprocess.run("git push origin HEAD", cwd=DB_DIR, shell=True, timeout=300)
            except: print("   ⚠️ DB Sync Timeout")

    print("\n✨ อัปโหลดเสร็จสมบูรณ์! เชิญเช็กที่หน้าแอปได้เลยครับ")
    time.sleep(2)

if __name__ == "__main__":
    main()