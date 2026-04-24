import os
import subprocess
from PyPDF2 import PdfReader, PdfWriter

# ==========================================
# ⚙️ SETTINGS FOR PROCESS ZONE
# ==========================================
process_path = r'C:\Process_Zone'
gs_path = r'C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe'
MAX_FILE_SIZE_MB = 95

def compress_pdf(input_path):
    temp_output = input_path.replace(".pdf", "_temp.pdf")
    gs_command = [
        gs_path, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH',
        f'-sOutputFile={temp_output}', input_path
    ]
    try:
        subprocess.run(gs_command, check=True)
        if os.path.exists(temp_output):
            if os.path.getsize(temp_output) < os.path.getsize(input_path):
                os.remove(input_path)
                os.rename(temp_output, input_path)
                return True
            os.remove(temp_output)
    except Exception as e:
        print(f"   ❌ Error Compressing: {e}")
    return False

def split_pdf(input_path):
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(input_path)[0]
    parts = 2
    pages_per_part = total_pages // parts
    
    print(f"   ✂️ Splitting: {os.path.basename(input_path)}")
    for i in range(parts):
        writer = PdfWriter()
        start_page = i * pages_per_part
        end_page = (i + 1) * pages_per_part if i < parts - 1 else total_pages
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        output_filename = f"{base_name} เล่ม {i+1}.pdf"
        with open(output_filename, "wb") as f:
            writer.write(f)
    os.remove(input_path)
    print(f"   ✅ Split into {parts} parts successfully.")

def main():
    print(f"🛠 [Process Zone] Starting file preparation...")
    if not os.path.exists(process_path):
        os.makedirs(process_path)
        print(f"Created {process_path}. Please put your files there and run again.")
        return

    for root, dirs, files in os.walk(process_path):
        for file_name in files:
            if file_name.lower().endswith('.pdf'):
                full_path = os.path.join(root, file_name)
                f_size_mb = os.path.getsize(full_path) / (1024 * 1024)

                if f_size_mb > MAX_FILE_SIZE_MB:
                    print(f"🔍 Found large file: {file_name} ({f_size_mb:.2f} MB)")
                    compress_pdf(full_path)
                    
                    # เช็คขนาดหลังบีบอีกครั้ง
                    f_size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    if f_size_mb > MAX_FILE_SIZE_MB:
                        split_pdf(full_path)
                    else:
                        print(f"   ✅ Compression was enough.")

    print(f"\n✨ [Process Zone] All files are ready to be moved to Library!")

if __name__ == "__main__":
    main()