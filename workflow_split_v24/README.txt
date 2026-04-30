WORKFLOW SPLIT v2.4

สิ่งที่เปลี่ยนใน v2.4
- ย้าย state/manifest ออกจากห้องใน MyLibrary ไปไว้ที่ state_root กลาง
- ไม่มีการสร้าง .room_manifest.json ในแต่ละ repo อีกแล้ว
- สร้าง state_root และ archive_root ให้อัตโนมัติ ไม่ต้องสร้างเอง
- ตรวจ duplicate ข้ามทั้ง MyLibrary โดยดูประเภทไฟล์ + ขนาดไฟล์ และใช้ hash ยืนยัน
- บีบ PDF เมื่อเกิน max_pdf_mb
- กันไฟล์ที่ยังเกิน max_git_file_mb
- แบ่ง push เป็น batch ตามจำนวนไฟล์และขนาดรวม
- ย้ายไฟล์ที่ ingest สำเร็จออกจาก Process_Zone ไป Archive

โฟลเดอร์ที่โค้ดสร้างให้เอง
- state_root เช่น C:\\MyBook_Test\\workflow_state
- archive_root เช่น C:\\MyBook_Test\\workflow_archive
- logs_root ถ้ายังไม่มี

ลำดับใช้งาน
1) แก้ workflow_config.json ให้ path ตรงเครื่อง
2) เอาไฟล์ใหม่ไปวางใน Process_Zone ตามห้อง
3) python ingest_rooms.py
4) python build_indexes.py
5) python sync_changed_repos.py
หรือใช้ python run_all.py

หมายเหตุ
- ถ้าคุณมี .room_manifest.json เก่าค้างอยู่ใน repo ห้องต่าง ๆ ให้ลบออกเองครั้งเดียวก่อนเริ่มใช้ v2.4
- หลังจากนั้น v2.4 จะไม่สร้างไฟล์นี้อีก
