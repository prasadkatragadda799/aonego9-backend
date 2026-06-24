from pydantic import BaseModel


class KpiPoint(BaseModel):
    label: str
    value: float


class DashboardKpis(BaseModel):
    total_vendors: int
    pending_approvals: int
    total_users: int
    total_bookings: int
    active_bookings: int
    total_revenue: float
    monthly_revenue: float
    commission_earned: float


class VendorDashboardKpis(BaseModel):
    total_bookings: int
    active_bookings: int
    pending_requests: int
    completed_bookings: int
    total_earned: float
    pending_payout: float
    average_rating: float
    unread_notifications: int


class TrendData(BaseModel):
    points: list[KpiPoint]


class CategoryShare(BaseModel):
    shares: list[KpiPoint]
