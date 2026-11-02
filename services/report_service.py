"""
REPORT SERVICE - Thống kê doanh thu & báo cáo
"""

import database as db


class ReportService:

    @staticmethod
    def get_dashboard_stats() -> dict:
        return db.get_dashboard_stats()

    @staticmethod
    def get_revenue_by_6months() -> tuple:
        return db.get_revenue_by_6months()

    @staticmethod
    def get_revenue_stats() -> list:
        return db.get_revenue_stats()

    @staticmethod
    def get_overdue_orders() -> list:
        return db.get_overdue_orders()
