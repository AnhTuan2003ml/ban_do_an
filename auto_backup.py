import os
import shutil
import time
import json
from datetime import datetime
import threading
import sys
import requests

# Lấy port từ tham số dòng lệnh
PORT = sys.argv[1] if len(sys.argv) > 1 else "5000"
IS_MASTER = PORT == "5000"

# Thư mục lưu trữ backup
BACKUP_DIR = f"backups/master" if IS_MASTER else f"backups/slave_{PORT}"
# Danh sách các file cần backup
DATA_FILES = ["foods", "orders", "users"]
INTERVAL = 60  # Thời gian giữa các lần backup (tính bằng giây)
MAX_BACKUPS = 5  # Số lượng backup tối đa giữ lại
MASTER_URL = "http://127.0.0.1:5000"

# Đảm bảo thư mục backup tồn tại
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def clean_old_backups():
    """Xóa các backup cũ, chỉ giữ lại MAX_BACKUPS bản mới nhất"""
    if not os.path.exists(BACKUP_DIR):
        return
        
    # Lấy danh sách các thư mục backup
    backup_dirs = [d for d in os.listdir(BACKUP_DIR) 
                  if os.path.isdir(os.path.join(BACKUP_DIR, d))]
    
    # Sắp xếp theo thời gian tạo (mới nhất lên đầu)
    backup_dirs.sort(reverse=True)
    
    # Xóa các backup cũ
    for old_dir in backup_dirs[MAX_BACKUPS:]:
        old_path = os.path.join(BACKUP_DIR, old_dir)
        try:
            shutil.rmtree(old_path)
            print(f"🗑️ Đã xóa backup cũ: {old_path}")
        except Exception as e:
            print(f"❌ Lỗi khi xóa backup cũ {old_path}: {str(e)}")

def backup_data():
    """Tạo bản sao lưu cho tất cả các file dữ liệu"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_success = False
    
    # Tạo thư mục backup với timestamp
    backup_dir = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup từng file dữ liệu
    for data_type in DATA_FILES:
        try:
            # Đọc dữ liệu từ file local của node hiện tại
            source_file = os.path.join("master" if IS_MASTER else f"slave_{PORT}", f"{data_type}.json")
            if os.path.exists(source_file):
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Lưu vào file backup với timestamp
                backup_file = os.path.join(backup_dir, f"{data_type}.json")
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"✅ Node {PORT} đã tạo bản sao lưu {data_type}: {backup_file}")
                backup_success = True
            else:
                print(f"⚠️ File {source_file} không tồn tại")
            
        except Exception as e:
            print(f"❌ Node {PORT} lỗi khi backup {data_type}: {str(e)}")
    
    if backup_success:
        # Xóa các backup cũ
        clean_old_backups()
    else:
        print(f"❌ Node {PORT} không có file nào được sao lưu!")

def start_backup():
    """Chạy backup tự động trong luồng riêng."""
    def backup_loop():
        node_type = "Master" if IS_MASTER else f"Slave {PORT}"
        print(f"🔹 {node_type} bắt đầu tự động sao lưu dữ liệu... 🔹")
        print(f"📁 Thư mục backup: {BACKUP_DIR}")
        print(f"📄 Các file được backup: {', '.join(DATA_FILES)}")
        print(f"⏱️ Tần suất backup: mỗi {INTERVAL} giây")
        print(f"📦 Giữ lại {MAX_BACKUPS} bản backup mới nhất")
        print(f"⏳ Đợi 20 giây trước khi bắt đầu backup...")
        
        # Đợi 20 giây trước khi bắt đầu backup
        for i in range(20, 0, -1):
            print(f"⏳ Còn {i} giây...", end='\r')
            time.sleep(1)
        print("\n✅ Bắt đầu backup!")
        
        while True:
            backup_data()
            time.sleep(INTERVAL)
    
    backup_thread = threading.Thread(target=backup_loop, daemon=True)
    backup_thread.start()

if __name__ == "__main__":
    start_backup()
    # Giữ chương trình chạy
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n⚠️ Node {PORT} đã dừng backup")
