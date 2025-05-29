import json
import requests
from flask import Flask, request, jsonify # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore

app = Flask(__name__)

# Danh sách các node phụ (mô phỏng trên localhost)
SLAVE_NODES = ["http://127.0.0.1:5001", "http://127.0.0.1:5002"]

def load_food_items():
    """ Đọc danh sách đồ ăn từ file JSON """
    try:
        with open('master/foods.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Không tìm thấy file master/foods.json")
        return {}
    except json.JSONDecodeError:
        print("Lỗi định dạng file master/foods.json")
        return {}

def load_users():
    """ Đọc thông tin người dùng từ file JSON """
    try:
        with open('master/users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Không tìm thấy file master/users.json")
        return {}
    except json.JSONDecodeError:
        print("Lỗi định dạng file master/users.json")
        return {}

def save_users(users):
    """ Lưu thông tin người dùng vào file JSON """
    try:
        with open('master/users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi khi lưu file master/users.json: {e}")

def load_orders():
    """ Đọc thông tin đơn hàng từ file JSON """
    try:
        with open('master/orders.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Không tìm thấy file master/orders.json")
        return {}
    except json.JSONDecodeError:
        print("Lỗi định dạng file master/orders.json")
        return {}

def save_orders(orders):
    """ Lưu thông tin đơn hàng vào file JSON """
    try:
        with open('master/orders.json', 'w', encoding='utf-8') as f:
            json.dump(orders, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi khi lưu file master/orders.json: {e}")

# Khởi tạo dữ liệu từ các file JSON
FOOD_ITEMS = load_food_items()
USERS = load_users()
ORDERS = load_orders()

def sync_data():
    """ Gửi dữ liệu hiện tại đến các node phụ """
    data = {
        "users": USERS,
        "orders": ORDERS,
        "foods": FOOD_ITEMS
    }
    for node in SLAVE_NODES:
        try:
            response = requests.post(f"{node}/sync", json=data)
            if response.status_code == 200:
                print(f"Đồng bộ thành công với {node}")
            else:
                print(f"Lỗi đồng bộ với {node}: {response.text}")
        except requests.exceptions.RequestException:
            print(f"Không thể kết nối với {node}")

@app.route("/register", methods=["POST"])
def register():
    """ API đăng ký tài khoản """
    data = request.json
    if not all(k in data for k in ["username", "password", "email"]):
        return jsonify({"error": "Thiếu thông tin đăng ký"}), 400
    
    username = data["username"]
    if username in USERS:
        return jsonify({"error": "Tên đăng nhập đã tồn tại"}), 400
    
    hashed_password = generate_password_hash(data["password"])
    
    USERS[username] = {
        "username": username,
        "password": hashed_password,
        "email": data["email"]
    }
    
    # Khởi tạo đơn hàng trống cho người dùng mới
    ORDERS[username] = {}
    
    save_users(USERS)
    save_orders(ORDERS)
    sync_data()
    
    return jsonify({"message": "Đăng ký thành công!", "username": username})

@app.route("/login", methods=["POST"])
def login():
    """ API đăng nhập """
    data = request.json
    if not all(k in data for k in ["username", "password"]):
        return jsonify({"error": "Thiếu thông tin đăng nhập"}), 400
    
    username = data["username"]
    if username not in USERS:
        return jsonify({"error": "Tên đăng nhập không tồn tại"}), 401
    
    user = USERS[username]
    if check_password_hash(user["password"], data["password"]):
        return jsonify({
            "message": "Đăng nhập thành công!",
            "username": username
        })
    
    return jsonify({"error": "Mật khẩu không đúng"}), 401

@app.route("/foods", methods=["GET"])
def list_foods():
    """ API lấy danh sách đồ ăn mặc định của hệ thống """
    return jsonify(FOOD_ITEMS)

@app.route("/users", methods=["GET"])
def list_users():
    """ API lấy danh sách người dùng """
    return jsonify(USERS)

@app.route("/orders", methods=["GET"])
def list_orders():
    """ API lấy danh sách đơn hàng """
    return jsonify(ORDERS)

@app.route("/user/<username>/orders", methods=["GET"])
def get_user_orders(username):
    """ API lấy danh sách đồ ăn đã đặt của người dùng """
    if username not in USERS:
        return jsonify({"error": "Người dùng không tồn tại"}), 404
    
    user_orders = ORDERS.get(username, {})
    order_items = []
    total = 0
    
    for food_id, quantity in user_orders.items():
        if food_id in FOOD_ITEMS:
            food = FOOD_ITEMS[food_id]
            item_total = food["price"] * quantity
            order_items.append({
                "food_id": food_id,
                "name": food["name"],
                "price": food["price"],
                "quantity": quantity,
                "total": item_total
            })
            total += item_total
    
    return jsonify({
        "items": order_items,
        "total": total
    })

@app.route("/user/<username>/order/add", methods=["POST"])
def add_food_to_order(username):
    """ API thêm đồ ăn vào đơn hàng của người dùng """
    if username not in USERS:
        return jsonify({"error": "Người dùng không tồn tại"}), 404
    
    data = request.json
    if not all(k in data for k in ["food_id", "quantity"]):
        return jsonify({"error": "Thiếu thông tin"}), 400
    
    food_id = data["food_id"]
    quantity = int(data["quantity"])
    
    if food_id not in FOOD_ITEMS:
        return jsonify({"error": "Món ăn không tồn tại"}), 404
    
    if quantity <= 0:
        return jsonify({"error": "Số lượng phải lớn hơn 0"}), 400
    
    if username not in ORDERS:
        ORDERS[username] = {}
    
    ORDERS[username][food_id] = ORDERS[username].get(food_id, 0) + quantity
    save_orders(ORDERS)
    sync_data()
    
    return jsonify({
        "message": "Thêm vào đơn hàng thành công!",
        "orders": ORDERS[username]
    })

@app.route("/user/<username>/order/remove", methods=["POST"])
def remove_food_from_order(username):
    """ API xóa đồ ăn khỏi đơn hàng của người dùng """
    if username not in USERS:
        return jsonify({"error": "Người dùng không tồn tại"}), 404
    
    data = request.json
    if "food_id" not in data:
        return jsonify({"error": "Thiếu thông tin"}), 400
    
    food_id = data["food_id"]
    
    if username in ORDERS and food_id in ORDERS[username]:
        del ORDERS[username][food_id]
        save_orders(ORDERS)
        sync_data()
        return jsonify({
            "message": "Xóa khỏi đơn hàng thành công!",
            "orders": ORDERS[username]
        })
    
    return jsonify({"error": "Món ăn không có trong đơn hàng"}), 404

@app.route("/user/<username>/order/update", methods=["POST"])
def update_food_quantity(username):
    """ API cập nhật số lượng đồ ăn trong đơn hàng """
    if username not in USERS:
        return jsonify({"error": "Người dùng không tồn tại"}), 404
    
    data = request.json
    if not all(k in data for k in ["food_id", "quantity"]):
        return jsonify({"error": "Thiếu thông tin"}), 400
    
    food_id = data["food_id"]
    quantity = int(data["quantity"])
    
    if quantity <= 0:
        return jsonify({"error": "Số lượng phải lớn hơn 0"}), 400
    
    if username in ORDERS and food_id in ORDERS[username]:
        ORDERS[username][food_id] = quantity
        save_orders(ORDERS)
        sync_data()
        return jsonify({
            "message": "Cập nhật số lượng thành công!",
            "orders": ORDERS[username]
        })
    
    return jsonify({"error": "Món ăn không có trong đơn hàng"}), 404

@app.route("/sync", methods=["POST"])
def api_sync():
    """ API nhận dữ liệu từ Master để đồng bộ """
    data = request.json
    global USERS, ORDERS
    
    if "users" in data:
        USERS = data["users"]
        save_users(USERS)
    
    if "orders" in data:
        ORDERS = data["orders"]
        save_orders(ORDERS)
    
    return jsonify({"message": "Đồng bộ thành công!"})

if __name__ == "__main__":
    import auto_backup
    import threading
    from datetime import datetime

    # Chạy master_backup trong một luồng riêng biệt
    backup_thread = threading.Thread(target=auto_backup.start_backup, daemon=True)
    backup_thread.start()

    # Chạy Flask server
    app.run(port=5000, debug=True)

