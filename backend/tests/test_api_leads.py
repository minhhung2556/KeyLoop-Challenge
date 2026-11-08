from datetime import datetime

VALID_MESSAGE = (
    "I would like a quote and a test drive for the Taycan this month please."
)


def _payload(**overrides):
    data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+84 123 456 789",
        "message": VALID_MESSAGE,
        "vehicleInterest": "Porsche Taycan",
    }
    data.update(overrides)
    return data


def test_create_lead_success(client):
    response = client.post("/api/v1/leads", json=_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert data["phone"] == "+84123456789"
    assert data["status"] == "new"
    assert "X-Request-ID" in response.headers


def test_create_lead_invalid_email(client):
    response = client.post("/api/v1/leads", json=_payload(email="not-an-email"))
    assert response.status_code == 422
    assert "request_id" in response.json()


def test_create_lead_invalid_phone(client):
    response = client.post("/api/v1/leads", json=_payload(phone="abc"))
    assert response.status_code == 422


def test_create_lead_message_too_short(client):
    response = client.post("/api/v1/leads", json=_payload(message="Too short"))
    assert response.status_code == 422


def test_create_lead_extra_field(client):
    payload = _payload()
    payload["hack"] = "nope"
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 422


def test_list_filter_search_and_pagination(client):
    client.post("/api/v1/leads", json=_payload(name="Alpha", email="a@example.com"))
    client.post(
        "/api/v1/leads",
        json=_payload(name="Beta", email="b@example.com", vehicleInterest="BMW i4"),
    )
    listed = client.get("/api/v1/leads")
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    searched = client.get("/api/v1/leads?q=BMW")
    assert searched.json()["total"] == 1
    page = client.get("/api/v1/leads?limit=1&offset=1")
    assert len(page.json()["items"]) == 1


def test_detail_and_activity_flow(client):
    created = client.post("/api/v1/leads", json=_payload()).json()
    lead_id = created["id"]
    missing = client.get("/api/v1/leads/does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["detail"]["error_code"] == "LEAD_NOT_FOUND"
    assert "request_id" in missing.json()

    first = client.post(
        f"/api/v1/leads/{lead_id}/activities",
        json={"type": "note", "summary": "Internal reminder"},
    )
    assert first.status_code == 201
    still_new = client.get(f"/api/v1/leads/{lead_id}")
    assert still_new.json()["status"] == "new"

    called = client.post(
        f"/api/v1/leads/{lead_id}/activities",
        json={"type": "call", "summary": "Called customer", "notes": "Left voicemail"},
    )
    assert called.status_code == 201
    detail = client.get(f"/api/v1/leads/{lead_id}")
    body = detail.json()
    assert body["status"] == "contacted"
    times = [datetime.fromisoformat(item["createdAt"]) for item in body["activities"]]
    assert times == sorted(times)

    empty = client.post(
        f"/api/v1/leads/{lead_id}/activities",
        json={"type": "call", "summary": ""},
    )
    assert empty.status_code == 422
    unknown = client.post(
        "/api/v1/leads/missing/activities",
        json={"type": "call", "summary": "Called customer"},
    )
    assert unknown.status_code == 404


def test_patch_status(client):
    lead_id = client.post("/api/v1/leads", json=_payload()).json()["id"]
    patched = client.patch(f"/api/v1/leads/{lead_id}", json={"status": "closed"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "closed"
    unknown = client.patch("/api/v1/leads/missing", json={"status": "closed"})
    assert unknown.status_code == 404


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
