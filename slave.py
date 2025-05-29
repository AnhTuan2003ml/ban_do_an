import os
import sys
import json
from flask import Flask, request, jsonify # type: ignore
from datetime import datetime

# Nhập cổng chạy cho node phụ (mặc định là 5001)
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001

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

app = Flask(__name__)

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

@app.route("/foods", methods=["GET"])
def list_foods():
    """API lấy danh sách đồ ăn"""
    return jsonify(load_data("foods"))

@app.route("/orders", methods=["GET"])
def list_orders():
    """API lấy danh sách đơn hàng"""
    return jsonify(load_data("orders"))

@app.route("/users", methods=["GET"])
def list_users():
    """API lấy danh sách người dùng"""
    return jsonify(load_data("users"))

@app.route("/user/<username>/orders", methods=["GET"])
def get_user_orders(username):
    """API lấy danh sách đồ ăn đã đặt của người dùng"""
    orders = load_data("orders")
    if username in orders:
        return jsonify(orders[username])
    return jsonify({"error": "Không tìm thấy đơn hàng"}), 404

if __name__ == "__main__":
    print(f"🔹 Slave node đang chạy trên cổng {PORT}...")
    print(f"📁 Thư mục dữ liệu: {SLAVE_DIR}")
    app.run(port=PORT, debug=True)
