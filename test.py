import requests
import time

MASTER_URL = "http://127.0.0.1:5000"

def test_add_user():
    """Test API thêm người dùng"""
    user_data = {"name": "Alice", "age": 25}
    response = requests.post(f"{MASTER_URL}/add_user", json=user_data)
    
    if response.status_code == 200:
        print("✅ Thêm người dùng thành công:", response.json())
    else:
        print("❌ Thêm người dùng thất bại:", response.text)

def test_list_users():
    """Test API lấy danh sách người dùng"""
    response = requests.get(f"{MASTER_URL}/list_users")
    
    if response.status_code == 200:
        users = response.json()
        print("✅ Danh sách người dùng:", users)
    else:
        print("❌ Lỗi khi lấy danh sách người dùng:", response.text)

def test_slave_sync():
    """Test đồng bộ dữ liệu với các node phụ"""
    SLAVE_NODES = ["http://127.0.0.1:5001", "http://127.0.0.1:5002"]
    
    # Chờ một lúc để Master hoàn thành việc đồng bộ
    time.sleep(2)

    for node in SLAVE_NODES:
        response = requests.get(f"{node}/list_users")
        
        if response.status_code == 200:
            print(f"✅ Đồng bộ thành công với {node}: {response.json()}")
        else:
            print(f"❌ Lỗi đồng bộ với {node}: {response.text}")

if __name__ == "__main__":
    print("\n🔹 Bắt đầu test Master Node 🔹\n")
    test_add_user()
    test_list_users()
    test_slave_sync()
    print("\n✅ Hoàn thành test Master Node! ✅\n")
