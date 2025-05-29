import requests
import time
import subprocess
import os
import signal
import sys

MASTER_URL = "http://127.0.0.1:5000"
SLAVE_NODES = ["http://127.0.0.1:5001", "http://127.0.0.1:5002"]
BACKUP_DIR = "backups"

def wait_for_server(url, max_retries=5, delay=2):
    """Đợi server khởi động sẵn sàng"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/foods")
            if response.status_code == 200:
                print(f"✅ Server {url} đã sẵn sàng")
                return True
        except requests.exceptions.ConnectionError:
            print(f"⏳ Đợi server {url} khởi động... (lần {i+1}/{max_retries})")
            time.sleep(delay)
    return False

def start_servers():
    print("\n🚀 Đang khởi động Master và Slaves...\n")
    
    # Tắt Flask debug mode để tránh reload không cần thiết
    master_process = subprocess.Popen(
        ["python", "master.py"],
        env={**os.environ, "FLASK_DEBUG": "0"}
    )
    
    # Chạy backup cho master
    master_backup_process = subprocess.Popen(
        ["python", "auto_backup.py", "5000"],
        env={**os.environ, "FLASK_DEBUG": "0"}
    )
    
    slave_processes = [
        subprocess.Popen(
            ["python", "slave.py", "5001"],
            env={**os.environ, "FLASK_DEBUG": "0"}
        ),
        subprocess.Popen(
            ["python", "slave.py", "5002"],
            env={**os.environ, "FLASK_DEBUG": "0"}
        ),
    ]
    
    # Chạy backup cho mỗi slave
    backup_processes = [
        subprocess.Popen(
            ["python", "auto_backup.py", "5001"],
            env={**os.environ, "FLASK_DEBUG": "0"}
        ),
        subprocess.Popen(
            ["python", "auto_backup.py", "5002"],
            env={**os.environ, "FLASK_DEBUG": "0"}
        ),
    ]
    
    # Đợi các server khởi động
    print("\n⏳ Đang đợi các server khởi động...")
    
    # Kiểm tra master
    if not wait_for_server(MASTER_URL):
        print("❌ Không thể kết nối đến master server")
        cleanup([master_process, master_backup_process] + slave_processes + backup_processes)
        sys.exit(1)
    
    # Kiểm tra slaves
    for node in SLAVE_NODES:
        if not wait_for_server(node):
            print(f"❌ Không thể kết nối đến slave server {node}")
            cleanup([master_process, master_backup_process] + slave_processes + backup_processes)
            sys.exit(1)
    
    print("\n✅ Tất cả các server đã sẵn sàng!")
    return master_process, slave_processes, backup_processes, master_backup_process

def cleanup(processes):
    """Dừng tất cả các tiến trình"""
    print("\n🛑 Đang dừng các tiến trình...\n")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

def test_register():
    print("\n🔹 Test đăng ký tài khoản 🔹")
    user_data = {
        "username": "testuser",
        "password": "testpass123",
        "email": "test@example.com"
    }
    response = requests.post(f"{MASTER_URL}/register", json=user_data)
    
    if response.status_code == 200:
        print("✅ Đăng ký thành công:", response.json())
    elif response.status_code == 400 and "đã tồn tại" in response.json().get("error", ""):
        print("ℹ️ Tài khoản đã tồn tại, tiếp tục test...")
    else:
        print("❌ Đăng ký thất bại:", response.text)

def test_login():
    print("\n🔹 Test đăng nhập 🔹")
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    response = requests.post(f"{MASTER_URL}/login", json=login_data)
    
    if response.status_code == 200:
        print("✅ Đăng nhập thành công:", response.json())
    else:
        print("❌ Đăng nhập thất bại:", response.text)

def test_list_foods():
    print("\n🔹 Test lấy danh sách đồ ăn 🔹")
    response = requests.get(f"{MASTER_URL}/foods")
    
    if response.status_code == 200:
        foods = response.json()
        print("✅ Danh sách đồ ăn:", foods)
    else:
        print("❌ Lỗi khi lấy danh sách đồ ăn:", response.text)

def test_add_food_to_order():
    print("\n🔹 Test thêm đồ ăn vào đơn hàng 🔹")
    order_data = {
        "food_id": "1",  # ID của món Phở bò
        "quantity": 2
    }
    response = requests.post(f"{MASTER_URL}/user/testuser/order/add", json=order_data)
    
    if response.status_code == 200:
        print("✅ Thêm đồ ăn thành công:", response.json())
    else:
        print("❌ Thêm đồ ăn thất bại:", response.text)

def test_update_food_quantity():
    print("\n🔹 Test cập nhật số lượng đồ ăn 🔹")
    update_data = {
        "food_id": "1",
        "quantity": 5
    }
    response = requests.post(f"{MASTER_URL}/user/testuser/order/update", json=update_data)
    
    if response.status_code == 200:
        print("✅ Cập nhật số lượng thành công:", response.json())
    else:
        print("❌ Cập nhật số lượng thất bại:", response.text)

def test_add_another_food():
    print("\n🔹 Test thêm món ăn khác 🔹")
    order_data = {
        "food_id": "2",  # ID của món Cơm sườn
        "quantity": 1
    }
    response = requests.post(f"{MASTER_URL}/user/testuser/order/add", json=order_data)
    
    if response.status_code == 200:
        print("✅ Thêm món ăn thành công:", response.json())
    else:
        print("❌ Thêm món ăn thất bại:", response.text)

def test_remove_food():
    print("\n🔹 Test xóa món ăn 🔹")
    remove_data = {
        "food_id": "2"
    }
    response = requests.post(f"{MASTER_URL}/user/testuser/order/remove", json=remove_data)
    
    if response.status_code == 200:
        print("✅ Xóa món ăn thành công:", response.json())
    else:
        print("❌ Xóa món ăn thất bại:", response.text)

def test_check_slave_sync():
    print("\n🔹 Kiểm tra đồng bộ dữ liệu với Slave nodes 🔹")
    time.sleep(2)  # Đợi đồng bộ
    
    # Lấy dữ liệu từ master
    master_foods = requests.get(f"{MASTER_URL}/foods").json()
    master_orders = requests.get(f"{MASTER_URL}/orders").json()
    master_users = requests.get(f"{MASTER_URL}/users").json()
    
    for node in SLAVE_NODES:
        print(f"\nKiểm tra đồng bộ với {node}:")
        
        # Kiểm tra đồng bộ foods
        response = requests.get(f"{node}/foods")
        if response.status_code == 200:
            slave_foods = response.json()
            if slave_foods == master_foods:
                print(f"✅ Đồng bộ foods thành công")
            else:
                print(f"❌ Dữ liệu foods không khớp với master")
                print(f"  - Master foods: {master_foods}")
                print(f"  - Slave foods: {slave_foods}")
        else:
            print(f"❌ Lỗi khi lấy foods từ slave")
        
        # Kiểm tra đồng bộ orders
        response = requests.get(f"{node}/orders")
        if response.status_code == 200:
            slave_orders = response.json()
            if slave_orders == master_orders:
                print(f"✅ Đồng bộ orders thành công")
            else:
                print(f"❌ Dữ liệu orders không khớp với master")
                print(f"  - Master orders: {master_orders}")
                print(f"  - Slave orders: {slave_orders}")
        else:
            print(f"❌ Lỗi khi lấy orders từ slave")
            
        # Kiểm tra đồng bộ users
        response = requests.get(f"{node}/users")
        if response.status_code == 200:
            slave_users = response.json()
            if slave_users == master_users:
                print(f"✅ Đồng bộ users thành công")
            else:
                print(f"❌ Dữ liệu users không khớp với master")
                print(f"  - Master users: {master_users}")
                print(f"  - Slave users: {slave_users}")
        else:
            print(f"❌ Lỗi khi lấy users từ slave")

def main():
    master_proc, slave_procs, backup_procs, master_backup_proc = start_servers()
    processes = [master_proc] + slave_procs + backup_procs + [master_backup_proc]
    
    try:
        test_register()
        test_login()
        test_list_foods()
        test_add_food_to_order()
        test_update_food_quantity()
        test_add_another_food()
        test_remove_food()
        test_check_slave_sync()
        print("\n✅ Hoàn thành tất cả bài test! ✅\n")
    
    except KeyboardInterrupt:
        print("\n⚠️ Test bị gián đoạn bởi người dùng")
    
    finally:
        time.sleep(20)
        cleanup(processes)

if __name__ == "__main__":
    main()
