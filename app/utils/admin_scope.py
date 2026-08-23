"""Helpers for city-scoped super-admin access."""

from sqlalchemy import or_
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.models.user import User


def admin_city(admin: User) -> str:
    return (admin.admin_city or "").strip()


def vendor_city_clause(admin: User, city_column: InstrumentedAttribute):
    """Filter vendors to an admin's city when admin_city is set."""
    city = admin_city(admin)
    if not city:
        return True
    return or_(city_column.ilike(f"%{city}%"), city_column == "")


def assert_admin_city_login(admin: User, login_city: str | None) -> None:
    """When an admin account is city-scoped, require matching city at login."""
    scoped = admin_city(admin)
    if not scoped:
        return
    provided = (login_city or "").strip()
    if not provided:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=f"This admin account is scoped to {scoped}. Enter your city to sign in.")
    if scoped.lower() not in provided.lower() and provided.lower() not in scoped.lower():
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=f"City mismatch — this desk is scoped to {scoped}.")
