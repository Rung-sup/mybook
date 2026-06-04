import os
import subprocess
import re

# ==========================================
# ⚙️ CONFIGURATION (ตั้งค่าพาธคลังหลักของคุณ)
# ==========================================
LIBRARY_ROOT = r'C:\MyLibrary'

def run_git(command, cwd):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=cwd
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, "", str(e)

print("🔍 [เริ่มระบบตรวจสอบความไม่ตรงกันระหว่างไฟล์ในคอมพิวเตอร์ กับ บน GitHub ออนไลน์]")
print("=====================================================================")

if not os.path.exists(LIBRARY_ROOT):
    print(f"❌ ไม่พบโฟลเดอร์ LIBRARY_ROOT: {LIBRARY_ROOT}")
    exit()

# ค้นหาโฟลเดอร์หมวดเพลง 7_music ทั้งหมดใน MyLibrary
all_folders = sorted(os.listdir(LIBRARY_ROOT))
target_repos = []

for folder in all_folders:
    repo_path = os.path.join(LIBRARY_ROOT, folder)
    if os.path.isdir(repo_path) and folder.startswith("7_") and os.path.exists(os.path.join(repo_path, ".git")):
        target_repos.append(repo_path)

print(f"📂 ตรวจพบ Repository หมวดเพลงทั้งหมด {len(target_repos)} ห้อง\n")

for repo_path in target_repos:
    repo_name = os.path.basename(repo_path)
    print(f"---------------------------------------------------------------------")
    print(f"📦 โฟลเดอร์ห้องเพลง: {repo_name}")
    print(f"---------------------------------------------------------------------")
    
    # ดึงประวัติล่าสุดจากออนไลน์มาอัปเดตตัวชี้วัดในเครื่อง (ไม่กระทบไฟล์จริง)
    run_git("git fetch origin", repo_path)
    
    #ดึงชื่อกิ่งปัจจุบัน (main หรือ master)
    _, branch, _ = run_git("git branch --show-current", repo_path)
    branch = branch.strip() if branch else "main"
    
    # -----------------------------------------------------------------
    # ส่วนที่ 1: หาไฟล์ที่มีในคอมพ์ แต่ไม่มีบน GitHub (Local Only)
    # -----------------------------------------------------------------
    # ดึงรายชื่อไฟล์ทั้งหมดที่ถูกบันทึก (Commit) อยู่บน GitHub ออนไลน์ในกิ่งปัจจุบัน
    code_remote, remote_files_raw, _ = run_git(f"git ls-tree -r origin/{branch} --name-only", repo_path)
    remote_files = set(remote_files_raw.splitlines()) if code_remote == 0 else set()
    
    # ดึงรายชื่อไฟล์จริงในคอมพิวเตอร์ปัจจุบัน (กรองเฉพาะ .mp3)
    local_files = set()
    for root, dirs, files in os.walk(repo_path):
        if '.git' in root:
            continue
        for f in files:
            if f.lower().endswith('.mp3'):
                rel_p = os.path.relpath(os.path.join(root, f), repo_path).replace('\\', '/')
                local_files.add(rel_p)
                
    # คำนวณหาความแตกต่าง
    local_only = sorted(list(local_files - remote_files))
    github_only = sorted(list(remote_files - local_files))
    
    # แสดงผลกรณีที่ 1: ในคอมพิวเตอร์มีไฟล์ แต่บน GitHub ไม่มี
    if local_only:
        print(f" 🔴 [มีเฉพาะในคอมพิวเตอร์ - บน GitHub ไม่มี] รวม {len(local_only)} ไฟล์:")
        for idx, rel_file in enumerate(local_only, 1):
            # แปลงกลับเป็น Directory / Full Path ของ Windows
            win_directory_path = os.path.join(repo_path, rel_file.replace('/', '\\'))
            print(f"   [{idx}] {win_directory_path}")
    else:
        print(" 🟢 ไม่มีไฟล์สัญชาติคอมพิวเตอร์ที่ตกหล่นบน GitHub")

    print("") # เว้นบรรทัด

    # แสดงผลกรณีที่ 2: บน GitHub มีไฟล์ แต่ในคอมพิวเตอร์ลบออกไปแล้ว (GitHub Only)
    if github_only:
        print(f" 🔵 [มีเฉพาะบน GitHub ออนไลน์ - ในคอมพิวเตอร์ไม่มีแล้ว] รวม {len(github_only)} ไฟล์:")
        for idx, rel_file in enumerate(github_only, 1):
            # จำลอง Directory / Full Path ที่ควรจะเป็นในเครื่อง
            win_directory_path = os.path.join(repo_path, rel_file.replace('/', '\\'))
            print(f"   [{idx}] {win_directory_path}")
    else:
        print(" 🟢 ไม่มีไฟล์ค้างบน GitHub ที่ในคอมพิวเตอร์ลบไปแล้ว")
        
    if not local_only and not github_only:
        print(" ✅ สรุปสถานะ: ข้อมูลทั้งสองฝั่งตรงกันสมบูรณ์แบบ 100%")
    print("")

print("=====================================================================")
print("🎉 ตรวจสอบเปรียบเทียบความไม่ตรงกันของระบบเสร็จสิ้นแล้วครับคุณ Runnara!")