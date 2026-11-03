"""End-to-end API smoke test for the user, vendor and super-admin flows.

Sends the exact payloads the Flutter apps send. Run against a FRESH database:

    export DATABASE_URL=sqlite+aiosqlite:///./smoke.db ENVIRONMENT=production \\
        SECRET_KEY=<long-random> ADMIN_EMAIL=admin@aonego9.com \\
        ADMIN_PASSWORD=Smoke-Test-Pass-91 OTP_DEBUG=false \\
        CORS_ORIGINS=http://localhost:8741
    rm -f smoke.db && alembic upgrade head && uvicorn app.main:app --port 8765 &
    python scripts/smoke_test.py
"""
import os
import httpx, json, sys, datetime
B = os.environ.get("SMOKE_BASE_URL", "http://localhost:8765/api/v1")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Smoke-Test-Pass-91")
c = httpx.Client(timeout=20)
ok = fail = 0
def check(name, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("  PASS", name)
    else: fail += 1; print("  FAIL", name, extra)
def H(t): return {"Authorization": f"Bearer {t}"}

print("== admin")
r = c.post(f"{B}/auth/login/admin", json={"email": "admin@aonego9.com", "password": ADMIN_PASSWORD}); check("admin login", r.status_code == 200, r.text)
A = H(r.json()["access_token"])
for p in ["/analytics/admin/dashboard", "/analytics/admin/trends", "/vendors/admin?page=1&page_size=100", "/users?page=1&page_size=100",
          "/bookings/admin?page=1&page_size=100", "/payments/admin?page=1&page_size=100", "/reviews/admin?page=1&page_size=100",
          "/support/admin?page=1&page_size=100", "/events/admin?page=1&page_size=100", "/cms/banners", "/cms/categories",
          "/subscriptions/admin/plans", "/subscriptions/admin/requests", "/subscriptions/admin/payment-info", "/bookings/admin/advance?status=pending",
          "/cms/newsletters", "/cms/ads", "/sessions/admin", "/cms/partners", "/cms/team", "/browse/leads", "/cms/social"]:
    r = c.get(B + p, headers=A); check(f"GET {p}", r.status_code == 200, f"{r.status_code} {r.text[:120]}")
r = c.post(f"{B}/cms/categories", headers=A, json={"name": "Choreographers", "slug": "choreographers", "active": True}); check("create category (slug sent)", r.status_code == 201, r.text)
cat = r.json()["id"]
r = c.post(f"{B}/cms/categories", headers=A, json={"name": "Stylists", "active": True}); check("create category (no slug)", r.status_code == 201 and r.json()["slug"] == "stylists", r.text)
r = c.post(f"{B}/cms/categories", headers=A, json={"name": "Stylists", "active": True}); check("duplicate category -> 409", r.status_code == 409, r.text)
r = c.patch(f"{B}/cms/categories/{cat}/toggle", headers=A); check("toggle category", r.status_code == 200 and r.json()["active"] is False, r.text)
r = c.post(f"{B}/cms/banners", headers=A, json={"title": "Wedding season", "placement": "home_hero", "active": True, "image_url": "https://x/y.jpg", "link_url": "https://aonego9.com"}); check("create banner", r.status_code == 201 and r.json()["link_url"] == "https://aonego9.com", r.text)
bid = r.json()["id"]
r = c.put(f"{B}/cms/banners/{bid}", headers=A, json={"active": False}); check("toggle banner", r.status_code == 200 and r.json()["active"] is False, r.text)
r = c.delete(f"{B}/cms/banners/{bid}", headers=A); check("delete banner", r.status_code in (200, 204), r.text)
ev = {"title": "Casting Call", "category": "Fashion", "city": "Mumbai", "venue": "NSCI Dome", "description": "Open casting", "image_url": "https://x/e.jpg",
      "date": (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=10)).isoformat(), "status": "upcoming", "on_poster": True}
r = c.post(f"{B}/events/admin", headers=A, json=ev); check("create event with venue", r.status_code == 201 and r.json()["venue"] == "NSCI Dome", r.text)
eid = r.json()["id"]
r = c.put(f"{B}/events/admin/{eid}", headers=A, json={**ev, "venue": "Jio Centre"}); check("full edit event", r.status_code == 200 and r.json()["venue"] == "Jio Centre", r.text)
r = c.put(f"{B}/events/admin/{eid}", headers=A, json={"status": "live"}); check("status-only edit event", r.status_code == 200 and r.json()["status"] == "live", r.text)
r = c.get(f"{B}/events"); check("public events expose venue", any(e.get("venue") == "Jio Centre" for e in r.json()), r.text[:200])
r = c.get(f"{B}/settings/platform", headers=A); check("get platform settings", r.status_code == 200 and r.json()["commission_percent"] == 15, r.text)
r = c.put(f"{B}/settings/platform", headers=A, json={"commission_percent": 12, "auto_approve_kyc": True, "email_alerts": False, "payout_hold_hours": 0}); check("save platform settings", r.status_code == 200 and r.json()["commission_percent"] == 12, r.text)
r = c.post(f"{B}/admins/invite", headers=A, json={"email": "ops@aonego9.com", "name": "Ops Desk", "city": "Pune"}); check("invite admin", r.status_code == 201 and r.json()["temporary_password"], r.text)
temp = r.json()["temporary_password"]
r = c.get(f"{B}/admins", headers=A); check("list admins", r.status_code == 200 and len(r.json()) == 2, r.text)
r = c.post(f"{B}/auth/login/admin", json={"email": "ops@aonego9.com", "password": temp, "city": "Pune"}); check("invited admin signs in", r.status_code == 200, r.text)
r2 = c.post(f"{B}/admins/invite", headers=H(r.json()["access_token"]), json={"email": "x@aonego9.com", "name": "Xavier"}); check("city admin cannot invite", r2.status_code == 403, r2.text)

print("== vendor (production: registers as pending)")
r = c.post(f"{B}/auth/register/vendor", json={"name": "Priya Sharma", "company": "Spotlight Talent", "email": "priya@spot.in", "password": "Passw0rd!x", "phone": "", "city": "Mumbai", "category": "Female Models"}); check("register vendor", r.status_code == 201, r.text)
V = H(r.json()["access_token"])
r = c.get(f"{B}/vendors/me", headers=V); check("pending vendor reads own profile", r.status_code == 200 and r.json()["status"] == "pending", r.text)
r = c.post(f"{B}/auth/login/vendor", json={"email": "priya@spot.in", "password": "Passw0rd!x"}); check("pending vendor can sign in", r.status_code == 200, r.text)
r = c.post(f"{B}/vendors/me/roster", headers=V, json={"name": "Asha", "role": "Model", "city": "Mumbai", "day_rate": 25000, "rating": 0, "available": True, "shoots": 0}); check("roster day_rate saved", r.status_code == 201 and r.json()["day_rate"] == 25000, r.text)
r = c.post(f"{B}/vendors/me/packages", headers=V, json={"title": "Editorial", "category": "Models", "price": 45000, "unit": "per shoot", "description": "4 hours.", "active": True}); check("create package", r.status_code == 201, r.text)
for p in ["/analytics/vendor/dashboard", "/analytics/vendor/earnings-trend", "/vendors/me/packages", "/vendors/me/roster", "/vendors/me/portfolio",
          "/vendors/me/profile-details", "/bookings/vendor?page=1&page_size=100", "/payments/earnings?page=1&page_size=100", "/reviews/vendor?page=1&page_size=100",
          "/messages/threads", "/notifications", "/subscriptions/me", "/subscriptions/billing", "/subscriptions/requests/mine", "/subscriptions/payment-info"]:
    r = c.get(B + p, headers=V); check(f"GET {p}", r.status_code in (200, 404 if p == "/subscriptions/me" else 200), f"{r.status_code} {r.text[:120]}")
r = c.get(f"{B}/subscriptions/plans?audience=vendor"); check("public plans without login", r.status_code == 200, r.text)
vid = c.get(f"{B}/vendors/me", headers=V).json()["id"]

print("== vendor -> desk leads")
r = c.post(f"{B}/browse/leads", headers=V, json={"kind": "payout_request", "vendor_id": "FORGED", "amount": 5000, "message": "Payout please", "source": "vendor_console"}); check("signed lead accepted", r.status_code == 201, r.text)
d = r.json()["details"]; check("vendor_id stamped from token, not body", d.get("vendor_id") == vid and d.get("verified_sender") is True, json.dumps(d))
r = c.post(f"{B}/browse/leads", json={"kind": "payout_request", "vendor_id": "FORGED", "amount": 99999}); check("anonymous lead accepted", r.status_code == 201, r.text)
check("forged vendor_id stripped from anonymous lead", "vendor_id" not in r.json()["details"], json.dumps(r.json()["details"]))
r = c.get(f"{B}/browse/leads", headers=A); check("admin sees nested details", any(l["details"].get("vendor_id") == vid for l in r.json()), r.text[:200])

print("== admin acts on vendor")
r = c.put(f"{B}/vendors/admin/{vid}/status", headers=A, json={"status": "approved"}); check("approve vendor", r.status_code == 200, r.text)
r = c.put(f"{B}/vendors/admin/{vid}/kyc", headers=A, json={"kyc_verified": True}); check("verify KYC", r.status_code == 200, r.text)
r = c.post(f"{B}/payments/payout", headers=A, json={"vendor_id": vid, "amount": 5000}); check("record payout", r.status_code in (200, 201), r.text)
r = c.get(f"{B}/users?page=1&page_size=100", headers=A); check("users list excludes admins", all(u["email"] not in ("admin@aonego9.com", "ops@aonego9.com") for u in r.json()["items"]), r.text[:200])

print("== booking lifecycle")
r = c.post(f"{B}/browse/inquiry", json={"vendor_id": vid, "category": "Models", "name": "Rahul", "email": "rahul@x.in", "phone": "", "date": "2026-12-20", "message": "Shoot", "inquiry_ref": "AO9-123456"})
check("user inquiry creates booking", r.status_code in (200, 201), r.text[:200])
if r.status_code in (200, 201):
    bkid = r.json()["booking_id"]
    r = c.get(f"{B}/bookings/vendor?page=1&page_size=100", headers=V)
    check("vendor sees client contact", any(b["id"] == bkid and b["client_email"] == "rahul@x.in" and b["location"] == "" for b in r.json()["items"]), r.text[:300])
    r = c.put(f"{B}/bookings/{bkid}/quote", headers=V, json={"amount": 0}); check("zero quote -> 422", r.status_code == 422, r.text[:200])
    r = c.put(f"{B}/bookings/{bkid}/status", headers=V, json={"status": "confirmed"}); check("vendor -> confirmed", r.status_code == 200, r.text[:200])
    r = c.put(f"{B}/bookings/{bkid}/quote", headers=V, json={"amount": 40000}); check("vendor sets quote", r.status_code == 200 and r.json()["amount"] == 40000, r.text[:200])
    for s in ["inProgress", "completed"]:
        r = c.put(f"{B}/bookings/{bkid}/status", headers=V, json={"status": s}); check(f"vendor -> {s}", r.status_code == 200, r.text[:200])
    r = c.put(f"{B}/bookings/{bkid}/quote", headers=V, json={"amount": 50000}); check("quote locked after completion -> 409", r.status_code == 409, r.text[:200])
    pays = c.get(f"{B}/payments/admin?page=1&page_size=100", headers=A).json()["items"]
    mine = [p for p in pays if p["booking_id"] == bkid]
    check("completion records booking gross", any(p["type"] == "booking" and p["amount"] == 40000 for p in mine), mine)
    check("completion records 12% commission", any(p["type"] == "commission" and p["amount"] == 4800 for p in mine), mine)
    earn = c.get(f"{B}/payments/earnings?page=1&page_size=100", headers=V).json()["items"]
    check("vendor earning credited net of commission", any(e["booking_id"] == bkid and e["amount"] == 35200 and e["status"] == "settled" for e in earn), earn)
    r = c.put(f"{B}/bookings/{bkid}/status", headers=V, json={"status": "completed"}); check("re-complete rejected", r.status_code == 422, r.text[:200])
    pays = c.get(f"{B}/payments/admin?page=1&page_size=100", headers=A).json()["items"]
    check("no double ledger rows", sum(1 for p in pays if p["booking_id"] == bkid and p["type"] == "booking") == 1, pays)
    k = c.get(f"{B}/analytics/admin/dashboard", headers=A).json()
    check("dashboard revenue/commission from ledger", k["total_revenue"] == 40000 and k["monthly_revenue"] == 40000 and k["commission_earned"] == 4800, k)
    r = c.get(f"{B}/messages/threads", headers=V); check("inquiry opened a vendor thread", any(t["participant_name"] == "Rahul" and t["unread_count"] >= 1 for t in r.json()), r.text[:200])

print("== user app flows")
r = c.post(f"{B}/auth/register/user", json={"name": "Meera", "email": "meera@x.in", "password": "Passw0rd!x", "phone": "", "city": "Pune", "role": "client"}); check("register user", r.status_code == 201, r.text)
U = H(r.json()["access_token"])
r = c.post(f"{B}/auth/login/user", json={"email": "meera@x.in", "password": "Passw0rd!x"}); check("login user", r.status_code == 200, r.text)
for p in ["/users/me", "/bookings/me", "/subscriptions/plans?audience=user", "/subscriptions/payment-info", "/subscriptions/requests/mine",
          "/browse/categories", "/browse/listings?page=1&page_size=20", "/browse/ticker", "/browse/newsletters", "/browse/ads",
          "/browse/partners", "/browse/team", "/browse/updates", "/events", "/sessions", f"/vendors/public/{vid}",
          f"/vendors/public/{vid}/packages", f"/vendors/public/{vid}/portfolio", f"/vendors/public/{vid}/profile-details", f"/reviews/public/{vid}"]:
    r = c.get(B + p, headers=U); check(f"GET {p.split('?')[0]}", r.status_code == 200, f"{r.status_code} {r.text[:120]}")
inq = {"vendor_id": vid, "category": "Models", "name": "Meera", "email": "meera@x.in", "phone": "", "date": "2026-12-22", "message": "Lookbook", "urgent": False, "inquiry_ref": "AO9-222222", "phone_otp": ""}
r = c.post(f"{B}/browse/inquiry", json=inq); check("signed-out inquiry with a registered email -> 409", r.status_code == 409, r.text[:200])
r = c.post(f"{B}/browse/inquiry", headers=U, json=inq); check("signed-in inquiry goes to own account", r.status_code == 201, r.text[:200])
mb = r.json().get("booking_id")
r = c.get(f"{B}/bookings/me", headers=U); check("client sees own inquiry booking", any(b["id"] == mb for b in r.json()["items"]), r.text[:200])
r = c.post(f"{B}/bookings/advance", headers=U, json={"booking_id": mb, "inquiry_ref": "AO9-222222", "amount": 5000, "method": "UPI", "receipt_image": "https://x/r.jpg"}); check("client pays advance on own booking", r.status_code == 201, r.text[:200])
r = c.get(f"{B}/bookings/admin/advance?status=pending", headers=A); check("admin sees pending advance", any(a["booking_id"] == mb for a in r.json()), r.text[:200])
adv = next(a for a in r.json() if a["booking_id"] == mb)
r = c.post(f"{B}/bookings/admin/advance/{adv['id']}/approve", headers=A, json={}); check("admin approves advance", r.status_code == 200, r.text[:200])
pays = c.get(f"{B}/payments/admin?page=1&page_size=100", headers=A).json()["items"]
check("approved advance in ledger", any(p["booking_id"] == mb and p["type"] == "advance" and p["amount"] == 5000 for p in pays), pays)
r = c.put(f"{B}/bookings/{mb}/status", headers=V, json={"status": "cancelled"}); check("vendor cancels paid booking", r.status_code == 200, r.text[:200])
pays = c.get(f"{B}/payments/admin?page=1&page_size=100", headers=A).json()["items"]
check("cancellation queues advance refund", any(p["booking_id"] == mb and p["type"] == "refund" and p["status"] == "pending" for p in pays), pays)

print("== messaging")
r = c.get(f"{B}/messages/me/threads", headers=U); check("client sees inquiry thread", r.status_code == 200 and len(r.json()) == 1 and r.json()[0]["vendor_name"] == "Spotlight Talent", r.text[:200])
th = r.json()[0]["id"]
r = c.get(f"{B}/messages/threads/{th}", headers=V); check("vendor opens thread", r.status_code == 200 and r.json()["messages"][0]["from_vendor"] is False, r.text[:200])
r = c.post(f"{B}/messages/threads/{th}/messages", headers=V, json={"text": "Thanks Meera, sharing a quote shortly."}); check("vendor replies", r.status_code == 201, r.text[:200])
r = c.post(f"{B}/messages/threads/{th}/messages", headers=V, json={"text": "   "}); check("vendor empty message -> 422", r.status_code == 422, r.text[:200])
r = c.get(f"{B}/messages/me/threads/{th}", headers=U); check("client reads reply", r.status_code == 200 and r.json()["messages"][-1]["from_vendor"] is True, r.text[:200])
r = c.post(f"{B}/messages/me/threads/{th}/messages", headers=U, json={"text": "Great, thank you!"}); check("client sends message", r.status_code == 201, r.text[:200])
r = c.post(f"{B}/messages/me/threads/{th}/messages", headers=U, json={"text": ""}); check("client empty message -> 422", r.status_code == 422, r.text[:200])
r = c.get(f"{B}/messages/threads", headers=V); check("vendor unread bumped", any(t["id"] == th and t["unread_count"] == 1 for t in r.json()), r.text[:200])
r = c.get(f"{B}/notifications", headers=V); check("vendor notified of message", r.status_code == 200 and "New message from Meera" in r.text, r.text[:200])
r = c.get(f"{B}/messages/me/threads/{th}", headers=V); check("vendor token cannot use client route", r.status_code in (401, 403), r.text[:200])

print("== support")
r = c.post(f"{B}/support", headers=U, json={"subject": "Refund query", "body": "When will my advance be refunded?", "priority": "high"}); check("client raises ticket", r.status_code == 201, r.text[:200])
tk = r.json()["id"]
r = c.post(f"{B}/support", headers=U, json={"subject": "Hi", "priority": "medium"}); check("too-short subject -> 422", r.status_code == 422, r.text[:200])
r = c.post(f"{B}/support", headers=U, json={"subject": "Hello there", "priority": "critical"}); check("bad priority -> 422", r.status_code == 422, r.text[:200])
r = c.get(f"{B}/support/admin?page=1&page_size=100", headers=A); check("admin sees ticket with requester", any(t["id"] == tk and t["requester_name"] == "Meera" for t in r.json()["items"]), r.text[:200])
r = c.put(f"{B}/support/admin/{tk}", headers=A, json={"status": "resolved"}); check("admin resolves ticket", r.status_code == 200 and r.json()["status"] == "resolved", r.text[:200])
r = c.put(f"{B}/support/admin/{tk}", headers=A, json={"status": "done"}); check("bad ticket status -> 422", r.status_code == 422, r.text[:200])
r = c.get(f"{B}/support/me", headers=U); check("client lists own tickets", r.status_code == 200, r.text[:200])
r = c.post(f"{B}/browse/newsletter/subscribe", json={"name": "Meera", "email": "meera@x.in", "phone": "", "city": "Pune"}); check("newsletter subscribe", r.status_code in (200, 201), r.text)
r = c.post(f"{B}/browse/newsletter/contribute", json={"author_name": "Meera", "author_email": "meera@x.in", "author_phone": "", "organisation": "Studio M", "role": "Editor", "credentials_url": "", "city": "Pune", "kind": "trend", "title": "Monsoon edits", "body": "Story", "image_url": ""})
check("user-app contribute form payload accepted", r.status_code == 201, r.text[:200])
r = c.post(f"{B}/browse/leads", json={"kind": "contact", "name": "Meera", "email": "meera@x.in", "message": "Hi"}); check("contact form lead", r.status_code == 201, r.text)

print("== subscription ledger")
paid = [p for p in c.get(f"{B}/subscriptions/plans?audience=user", headers=U).json() if p["price"] > 0]
r = c.post(f"{B}/subscriptions/request", headers=U, json={"plan_id": paid[0]["id"], "receipt_image": "https://x/r.jpg"}); check("client requests paid plan", r.status_code == 200, r.text[:200])
r = c.post(f"{B}/subscriptions/admin/requests/{r.json()['id']}/approve", headers=A, json={}); check("admin approves plan", r.status_code == 200, r.text[:200])
pays = c.get(f"{B}/payments/admin?page=1&page_size=100", headers=A).json()["items"]
check("subscription recorded in ledger", any(p["type"] == "subscription" and p["party"] == "Meera" and p["amount"] == paid[0]["price"] for p in pays), pays)

print("== guest inquiry -> claim account")
guest = {**inq, "email": "guest@x.in", "name": "Guest", "inquiry_ref": "AO9-333333"}
r = c.post(f"{B}/browse/inquiry", json=guest); check("guest inquiry (no phone)", r.status_code == 201, r.text[:200])
r = c.post(f"{B}/browse/inquiry", json={**guest, "inquiry_ref": "AO9-333334"}); check("second guest inquiry reuses guest record", r.status_code == 201, r.text[:200])
r = c.post(f"{B}/auth/register/user", json={"name": "Guest", "email": "guest@x.in", "password": "Passw0rd!x"}); check("claim without phone on record -> desk message", r.status_code == 409 and "desk" in r.text, r.text[:200])
print(f"\n{ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
