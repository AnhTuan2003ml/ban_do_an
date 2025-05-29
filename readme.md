# Hướng Dẫn Chạy Dự Án

Dự án này mô phỏng hệ thống **Master-Slave** sử dụng **PupDB** để quản lý và đồng bộ dữ liệu giữa nhiều node.

## 1️⃣ Cài đặt thư viện cần thiết
Trước khi chạy, đảm bảo bạn đã cài đặt các thư viện cần thiết bằng cách chạy lệnh sau:
```sh
pip install flask requests pupdb
```

## 2️⃣ Khởi động Master Node
Master node sẽ chạy trên cổng **5000**.
```sh
python master.py
```

## 3️⃣ Khởi động các Slave Nodes
Chạy hai node phụ trên các cổng khác nhau:
```sh
python slave.py 5001
```
```sh
python slave.py 5002
```

## 4️⃣ Chạy Test Script
Sau khi các node đã chạy, kiểm tra hệ thống bằng cách chạy test:
```sh
python auto_test.py
```

Test script sẽ:
- **Thêm người dùng vào Master Node** ✅
- **Lấy danh sách người dùng từ Master Node** 📋
- **Kiểm tra đồng bộ dữ liệu trên Slave Nodes** 🔄

## 5️⃣ Dừng hệ thống
Sau khi hoàn thành test, dừng tất cả các tiến trình bằng cách nhấn `CTRL + C` trong terminal.


## Triển Khai web
```sh
python master.py
```
```sh
python slave_app.py 5001
```
sau đó mở http://127.0.0.1:5001



