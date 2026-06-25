"""Approve all pending vendors and seed platform events for the ticker."""
import asyncio
from datetime import datetime, timezone, timedelta
from app.core.database import AsyncSessionLocal
from app.models.vendor import Vendor
from app.models.user import ApprovalStatus
from app.models.event import PlatformEvent, EventStatus
from sqlalchemy import select, update

async def fix():
    async with AsyncSessionLocal() as db:
        # Approve all pending vendors
        result = await db.execute(select(Vendor).where(Vendor.status == ApprovalStatus.pending))
        vendors = result.scalars().all()
        for v in vendors:
            v.status = ApprovalStatus.approved
            print(f"✓ Approved vendor: {v.name} ({v.company}) — {v.category} · {v.city}")

        # Seed platform events for the ticker if none exist
        existing = (await db.execute(select(PlatformEvent))).scalars().all()
        if not existing:
            now = datetime.now(timezone.utc)
            events = [
                PlatformEvent(id="EV-1", title="Summer Fashion Week 2026", category="Fashion Show", city="Mumbai",
                    date=now + timedelta(days=5), status=EventStatus.live, on_poster=True, registrations=1840),
                PlatformEvent(id="EV-2", title="AOneGo9 Talent Showcase", category="Showcase", city="Delhi",
                    date=now + timedelta(days=12), status=EventStatus.upcoming, on_poster=True, registrations=620),
                PlatformEvent(id="EV-3", title="Bridal & Wedding Expo", category="Expo", city="Bengaluru",
                    date=now + timedelta(days=21), status=EventStatus.upcoming, on_poster=True, registrations=410),
            ]
            for e in events:
                db.add(e)
            print(f"✓ Seeded {len(events)} platform events")
        else:
            print(f"  Events already exist ({len(existing)} found)")

        await db.commit()
        print("Done.")

asyncio.run(fix())
