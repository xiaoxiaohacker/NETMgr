from fastapi import APIRouter

# 定义路由前缀变量，避免硬编码
DASHBOARD_PREFIX = "/dashboard"

router = APIRouter(prefix=DASHBOARD_PREFIX)

@router.get("/stats")
def get_new_dashboard_stats():
    """New, completely independent dashboard stats endpoint"""
    return {
        "success": True,
        "message": "This is a test from the new dashboard module",
        "data": {
            "active_devices": 42,
            "total_traffic": "1.2 TB"
        }
    }