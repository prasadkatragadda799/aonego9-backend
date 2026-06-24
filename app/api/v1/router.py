from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    bookings,
    browse,
    cms,
    events,
    messages,
    notifications,
    payments,
    reviews,
    subscriptions,
    support,
    users,
    vendors,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(vendors.router)
api_router.include_router(bookings.router)
api_router.include_router(payments.router)
api_router.include_router(reviews.router)
api_router.include_router(messages.router)
api_router.include_router(notifications.router)
api_router.include_router(events.router)
api_router.include_router(cms.router)
api_router.include_router(subscriptions.router)
api_router.include_router(analytics.router)
api_router.include_router(support.router)
api_router.include_router(browse.router)
