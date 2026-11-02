# 💍 ÁO CƯỚI THANH HẰNG - Phần Mềm Quản Lý Cho Thuê Áo Cưới

## Cách chạy

```bash
cd wedding_rental_management
python main.py
```

## Cấu trúc dự án

```
wedding_rental_management/
├── main.py                  # Chương trình chính (GUI/menu)
├── database.py              # Kết nối & truy vấn SQLite
├── wedding_rental.db        # File cơ sở dữ liệu
├── requirements.txt
│
├── models/                  # Các lớp dữ liệu
│   ├── __init__.py
│   ├── dress.py             # Trang phục (nữ & nam)
│   ├── accessory.py         # Phụ kiện
│   ├── customer.py          # Khách hàng
│   └── order.py             # Đơn thuê
│
├── services/                # Xử lý nghiệp vụ
│   ├── __init__.py
│   ├── rental_service.py    # Xử lý thuê/trả & khách hàng
│   ├── inventory_service.py # Quản lý kho
│   └── report_service.py    # Thống kê doanh thu
│
├── utils/                   # Tiện ích
│   ├── __init__.py
│   ├── validators.py        # Kiểm tra dữ liệu
│   └── helpers.py           # Hàm hỗ trợ
│
└── exceptions/              # Xử lý lỗi
    ├── __init__.py
    └── rental_exceptions.py
```
