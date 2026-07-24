import os
from pathlib import Path

def rename_files_by_mtime_reverse(folder_path):
    folder = Path(folder_path)
    files = [f for f in folder.iterdir() if f.is_file()]
    # เรียงไฟล์ตามเวลาแก้ไขล่าสุด (mtime) จากล่าสุดไปเก่าสุด
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    for idx, file in enumerate(files, 1):
        ext = file.suffix
        new_name = f"{idx:03d}{ext}"
        new_path = file.with_name(new_name)
        file.rename(new_path)
    print(f"เปลี่ยนชื่อไฟล์ใน '{folder_path}' เรียบร้อยแล้ว!")

if __name__ == "__main__":
    # กำหนด path โฟลเดอร์ที่ต้องการแก้ไขชื่อไฟล์
    folder_path = r"E:\Revit\Test\RSV_DRAWING_COURSE\example home\6"
    rename_files_by_mtime_reverse(folder_path)
