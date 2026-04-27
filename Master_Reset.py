import os
import subprocess
import time

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'
GITHUB_USER = "Rung-sup"

def run_cmd(command, cwd):
    # สั่งรันคำสั่งโดยไม่ต้องโชว์ข้อความรกรุงรัง
    subprocess.run(command, shell=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def reset_repo(folder_path, repo_url, folder_name):
    print(f"\n🧹 กำลังล้างประวัติห้อง: {folder_name}...")
    git_dir = os.path.join(folder_path, '.git')
    
    # 1. ฆ่าเชื้อ: ลบโฟลเดอร์ .git ทิ้งเพื่อทำลายประวัติที่บวม
    if os.path.exists(git_dir):
        subprocess.run(f'rmdir /s /q "{git_dir}"', shell=True)
        time.sleep(1) # รอให้ระบบลบไฟล์เสร็จสมบูรณ์

    # 2. สร้างใหม่: สร้าง Git ใหม่และผูกกับ GitHub
    print(f"☁️ กำลังสร้างระบบใหม่และส่งขึ้น Cloud (อาจใช้เวลาสักครู่)...")
    run_cmd("git init", folder_path)
    run_cmd("git branch -M main", folder_path)
    run_cmd("git add .", folder_path)
    run_cmd('git commit -m "Master Reset: Clean History"', folder_path)
    run_cmd(f"git remote add origin {repo_url}", folder_path)
    
    # 3. ส่งขึ้นทับของเดิม: บังคับ Push ทับของเก่าบน GitHub (-f)
    result = subprocess.run("git push -u -f origin main", shell=True, cwd=folder_path, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ ห้อง {folder_name} สะอาดเอี่ยมและพร้อมใช้งาน!")
    else:
        print(f"   ⚠️ พบปัญหาในห้อง {folder_name} (อาจเกิดจากขนาดไฟล์เกินขีดจำกัด)")

def main():
    print("🚀 เริ่มปฏิบัติการ 'ล้างไพ่' ทำความสะอาดทุกห้อง...")

    # --- 1. ล้างห้องสมุดทั้งหมดใน MyLibrary ---
    for folder in os.listdir(LIBRARY_ROOT):
        folder_path = os.path.join(LIBRARY_ROOT, folder)
        if not os.path.isdir(folder_path): continue
        
        # สร้าง URL ของ GitHub ให้ตรงกับชื่อโฟลเดอร์อัตโนมัติ
        repo_url = f"https://github.com/{GITHUB_USER}/{folder}.git"
        reset_repo(folder_path, repo_url, folder)

    # --- 2. ล้างห้องฐานข้อมูล MyBook_Test ---
    repo_url_db = f"https://github.com/{GITHUB_USER}/mybook.git"
    reset_repo(DB_DIR, repo_url_db, "mybook (Database)")

    print("\n✨ ภารกิจเสร็จสิ้น! ทุกห้องได้รับการรีเซ็ตและมีขนาดเบาที่สุดแล้วครับ")
    time.sleep(3)

if __name__ == "__main__":
    main()