from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import sys
import threading
import auto_backup
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Lấy port từ tham số dòng lệnh hoặc mặc định là 5001
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
MASTER_URL = "http://127.0.0.1:5000"

# Thư mục lưu trữ dữ liệu chính
SLAVE_DIR = f"slave_{PORT}"

# Đảm bảo thư mục slave tồn tại
if not os.path.exists(SLAVE_DIR):
    os.makedirs(SLAVE_DIR)
    # Khởi tạo các file JSON rỗng
    for data_type in ["foods", "orders", "users"]:
        with open(os.path.join(SLAVE_DIR, f"{data_type}.json"), 'w', encoding='utf-8') as f:
            json.dump({}, f)

def load_data(data_type):
    """Đọc dữ liệu từ file trong thư mục slave"""
    file_path = os.path.join(SLAVE_DIR, f"{data_type}.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data_type, data):
    """Lưu dữ liệu vào file trong thư mục slave"""
    file_path = os.path.join(SLAVE_DIR, f"{data_type}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Khởi động backup trong một thread riêng
def start_backup():
    print(f"🔄 Bắt đầu quá trình backup cho slave node {PORT}...")
    auto_backup.start_backup()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/foods')
def get_foods():
    """Lấy danh sách đồ ăn từ dữ liệu local và đồng bộ từ master"""
    try:
        # Lấy dữ liệu từ master
        response = requests.get(f"{MASTER_URL}/foods")
        if response.status_code == 200:
            # Cập nhật dữ liệu local
            save_data("foods", response.json())
            return jsonify(response.json())
    except:
        # Nếu không kết nối được master, trả về dữ liệu local
        return jsonify(load_data("foods"))

@app.route('/api/register', methods=['POST'])
def register():
    """Chuyển tiếp yêu cầu đăng ký đến master"""
    try:
        response = requests.post(f"{MASTER_URL}/register", json=request.json)
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({"error": "Không thể kết nối đến master server"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Chuyển tiếp yêu cầu đăng nhập đến master"""
    try:
        response = requests.post(f"{MASTER_URL}/login", json=request.json)
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({"error": "Không thể kết nối đến master server"}), 500

@app.route('/api/user/<username>/orders')
def get_user_orders(username):
    """Lấy đơn hàng của người dùng từ dữ liệu local và đồng bộ từ master"""
    try:
        # Lấy dữ liệu từ master
        response = requests.get(f"{MASTER_URL}/user/{username}/orders")
        if response.status_code == 200:
            # Cập nhật dữ liệu local
            orders = load_data("orders")
            orders[username] = response.json()
            save_data("orders", orders)
            return jsonify(response.json())
    except:
        # Nếu không kết nối được master, trả về dữ liệu local
        orders = load_data("orders")
        if username in orders:
            return jsonify(orders[username])
    return jsonify({"error": "Không tìm thấy đơn hàng"}), 404

@app.route('/api/user/<username>/order/add', methods=['POST'])
def add_to_order(username):
    """Chuyển tiếp yêu cầu thêm vào đơn hàng đến master và cập nhật local"""
    try:
        response = requests.post(f"{MASTER_URL}/user/{username}/order/add", json=request.json)
        if response.status_code == 200:
            # Cập nhật dữ liệu local
            orders = load_data("orders")
            if username not in orders:
                orders[username] = {}
            food_id = request.json.get("food_id")
            quantity = request.json.get("quantity", 0)
            orders[username][food_id] = orders[username].get(food_id, 0) + quantity
            save_data("orders", orders)
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({"error": "Không thể kết nối đến master server"}), 500

@app.route('/api/user/<username>/order/remove', methods=['POST'])
def remove_from_order(username):
    """Chuyển tiếp yêu cầu xóa khỏi đơn hàng đến master và cập nhật local"""
    try:
        response = requests.post(f"{MASTER_URL}/user/{username}/order/remove", json=request.json)
        if response.status_code == 200:
            # Cập nhật dữ liệu local
            orders = load_data("orders")
            if username in orders:
                food_id = request.json.get("food_id")
                if food_id in orders[username]:
                    del orders[username][food_id]
                    save_data("orders", orders)
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({"error": "Không thể kết nối đến master server"}), 500

@app.route("/sync", methods=["POST"])
def sync_data():
    """API nhận dữ liệu từ master để đồng bộ"""
    data = request.json
    
    # Đồng bộ danh sách đồ ăn
    if "foods" in data:
        save_data("foods", data["foods"])
    
    # Đồng bộ danh sách đơn hàng
    if "orders" in data:
        save_data("orders", data["orders"])
    
    # Đồng bộ danh sách người dùng
    if "users" in data:
        save_data("users", data["users"])

    return jsonify({"message": "Đồng bộ thành công!"}), 200

if __name__ == '__main__':
    # Khởi động thread backup
    backup_thread = threading.Thread(target=start_backup, daemon=True)
    backup_thread.start()
    
    print(f"🔹 Slave web app đang chạy trên cổng {PORT}...")
    print(f"📁 Thư mục dữ liệu: {SLAVE_DIR}")
    print(f"🔄 Backup tự động đã được kích hoạt")
    app.run(port=PORT, debug=True) 