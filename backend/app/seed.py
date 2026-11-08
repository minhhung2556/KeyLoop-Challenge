from datetime import datetime, timedelta

from app.repositories.lead_repository import SQLiteLeadRepository


def seed_demo_leads(repo: SQLiteLeadRepository) -> None:
    if repo.count_leads() > 0:
        return
    base = datetime.utcnow()
    specs = [
        {
            "id": "seed-lead-1",
            "name": "Lan Nguyen",
            "email": "lan.nguyen@example.vn",
            "phone": "+84901112233",
            "message": "I would like a test drive of the 2026 Porsche Taycan this weekend.",
            "vehicleInterest": "2026 Porsche Taycan",
            "status": "new",
            "days_ago": 1,
            "activities": [],
        },
        {
            "id": "seed-lead-2",
            "name": "Minh Tran",
            "email": "minh.tran@example.vn",
            "phone": "+84987654321",
            "message": "Please send a lease quote for the BMW i4 M50 with winter tyres.",
            "vehicleInterest": "BMW i4 M50",
            "status": "new",
            "days_ago": 2,
            "activities": [],
        },
        {
            "id": "seed-lead-3",
            "name": "Sarah Chen",
            "email": "sarah.chen@example.com",
            "phone": "+6591234567",
            "message": "Interested in trading my Q5 for the new Audi Q6 e-tron.",
            "vehicleInterest": "Audi Q6 e-tron",
            "status": "contacted",
            "days_ago": 5,
            "activities": [
                {
                    "id": "seed-act-3-1",
                    "type": "call",
                    "summary": "Called customer",
                    "notes": "Left voicemail about trade-in valuation.",
                    "createdBy": "Alex Mercer",
                    "hours_after": 4,
                }
            ],
        },
        {
            "id": "seed-lead-4",
            "name": "Hoang Pham",
            "email": "hoang.pham@example.vn",
            "phone": "+84905556677",
            "message": "Need financing options for a Mercedes GLC 300 this quarter.",
            "vehicleInterest": "Mercedes-Benz GLC 300",
            "status": "contacted",
            "days_ago": 8,
            "activities": [
                {
                    "id": "seed-act-4-1",
                    "type": "email",
                    "summary": "Sent financing quote",
                    "notes": "Shared 36 and 48 month offers.",
                    "createdBy": "Alex Mercer",
                    "hours_after": 6,
                }
            ],
        },
        {
            "id": "seed-lead-5",
            "name": "Emily Watson",
            "email": "emily.w@example.com",
            "phone": "+447700900123",
            "message": "Thanks, we completed the Mini Cooper SE purchase last week.",
            "vehicleInterest": "MINI Cooper SE",
            "status": "closed",
            "days_ago": 14,
            "activities": [
                {
                    "id": "seed-act-5-1",
                    "type": "call",
                    "summary": "Called customer",
                    "notes": "Confirmed handover complete.",
                    "createdBy": "Alex Mercer",
                    "hours_after": 2,
                },
                {
                    "id": "seed-act-5-2",
                    "type": "note",
                    "summary": "Closed won",
                    "notes": "No further follow-up required.",
                    "createdBy": "Alex Mercer",
                    "hours_after": 26,
                },
            ],
        },
        {
            "id": "seed-lead-6",
            "name": "Duc Le",
            "email": "duc.le@example.vn",
            "phone": "+84908889900",
            "message": "Can I book a Hyundai Ioniq 6 test drive after work on Friday?",
            "vehicleInterest": "Hyundai Ioniq 6",
            "status": "new",
            "days_ago": 0,
            "activities": [],
        },
    ]
    for spec in specs:
        created = base - timedelta(days=spec["days_ago"], hours=1)
        lead = {
            "id": spec["id"],
            "name": spec["name"],
            "email": spec["email"],
            "phone": spec["phone"],
            "message": spec["message"],
            "vehicleInterest": spec["vehicleInterest"],
            "status": spec["status"],
            "createdAt": created.isoformat(),
        }
        activities = []
        for act in spec["activities"]:
            activities.append(
                {
                    "id": act["id"],
                    "type": act["type"],
                    "summary": act["summary"],
                    "notes": act.get("notes"),
                    "createdBy": act["createdBy"],
                    "createdAt": (created + timedelta(hours=act["hours_after"])).isoformat(),
                }
            )
        repo.insert_seed_lead(lead, activities)
