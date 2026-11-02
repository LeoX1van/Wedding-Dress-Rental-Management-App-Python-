"""
INVENTORY SERVICE - Quản lý kho trang phục & phụ kiện
"""

import database as db
from models.dress import Dress
from models.accessory import Accessory
from exceptions.rental_exceptions import ValidationError
from utils.validators import validate_required, validate_positive_number


class InventoryService:

    @staticmethod
    def get_all_products(category=None):
        rows = db.get_all_products(category)
        results = []
        for r in rows:
            if r.get("category") == "phu_kien":
                results.append(Accessory.from_dict(r))
            else:
                results.append(Dress.from_dict(r))
        return results

    @staticmethod
    def get_available_products(category=None):
        rows = db.get_available_products(category)
        results = []
        for r in rows:
            if r.get("category") == "phu_kien":
                results.append(Accessory.from_dict(r))
            else:
                results.append(Dress.from_dict(r))
        return results

    @staticmethod
    def add_product(code, name, category, ptype, size, color,
                    price_per_day, deposit, description):
        validate_required(code, "Mã sản phẩm")
        validate_required(name, "Tên sản phẩm")
        validate_positive_number(str(price_per_day), "Giá thuê/ngày", allow_zero=False)
        return db.add_product(code.strip(), name.strip(), category, ptype,
                              size, color, float(price_per_day),
                              float(deposit or 0), description)

    @staticmethod
    def update_product(pid, code, name, category, ptype, size, color,
                       price_per_day, deposit, description, status):
        validate_required(code, "Mã sản phẩm")
        validate_required(name, "Tên sản phẩm")
        validate_positive_number(str(price_per_day), "Giá thuê/ngày", allow_zero=False)
        db.update_product(pid, code.strip(), name.strip(), category, ptype,
                          size, color, float(price_per_day),
                          float(deposit or 0), description, status)

    @staticmethod
    def delete_product(pid):
        db.delete_product(pid)
