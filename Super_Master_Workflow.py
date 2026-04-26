# --- [ปรับปรุงส่วนท้ายของ Step 3 ในสคริปต์ V1.4] ---
    print("☁️ [3/3] กำลังทยอยส่งข้อมูลขึ้น Cloud...")
    
    # ... (ส่วนส่ง MyLibrary เหมือนเดิม) ...

    # ส่วนส่ง MyBook_Test (ฐานข้อมูล)
    if os.path.exists(os.path.join(DB_DIR, ".git")):
        print("💾 กำลังส่งฐานข้อมูลแอป...")
        run_git("git add .", DB_DIR)
        status = run_git("git status --porcelain", DB_DIR)
        if status:
            run_git('git commit -m "Final Auto-Sync"', DB_DIR)
            # เพิ่มการเช็กเพื่อให้แน่ใจว่า Push แล้วจบงาน
            subprocess.run("git push origin HEAD", cwd=DB_DIR, shell=True, timeout=60) 
            print("   ✅ อัปเดต Repo MyBook สำเร็จ!")
        else:
            print("   ✅ ไม่มีข้อมูลใหม่ต้องอัปเดต")

    # บังคับจบการทำงานของสคริปต์ทั้งหมด
    print("\n✨ [ภารกิจเสร็จสมบูรณ์] ระบบกำลังปิดตัวลง...")
    os._exit(0) # สั่งให้ Python คืนสิทธิ์ให้ระบบทันทีโดยไม่ต้องรอ