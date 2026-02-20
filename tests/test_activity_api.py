from app.schemas import ActivityLogCreateSchema, ActivityLogResponseSchema


def test_create_activity_log(test_client, user_payload, activity_payload):
    test_client.post("/api/users/", json=user_payload)

    response = test_client.post("/api/activity/", json=activity_payload)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["Status"] == "Success"
    assert response_json["Log"]["action"] == "login"
    assert response_json["Log"]["description"] == "User logged in from web browser"
    assert response_json["Log"]["ip_address"] == "192.168.1.1"


def test_create_activity_log_user_not_found(test_client, activity_payload):
    response = test_client.post("/api/activity/", json=activity_payload)
    assert response.status_code == 404


def test_get_user_activity_logs(test_client, user_payload, activity_payload):
    test_client.post("/api/users/", json=user_payload)

    test_client.post("/api/activity/", json=activity_payload)
    activity_payload_2 = activity_payload.copy()
    activity_payload_2["action"] = "LOGOUT"
    activity_payload_2["description"] = "User logged out"
    test_client.post("/api/activity/", json=activity_payload_2)

    response = test_client.get(f"/api/activity/user/{user_payload['id']}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"] == "Success"
    assert response_json["results"] == 2


def test_get_activity_log_by_id(test_client, user_payload, activity_payload):
    test_client.post("/api/users/", json=user_payload)

    create_response = test_client.post("/api/activity/", json=activity_payload)
    log_id = create_response.json()["Log"]["id"]

    response = test_client.get(f"/api/activity/{log_id}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["Status"] == "Success"
    assert response_json["Log"]["id"] == log_id


def test_get_activity_log_not_found(test_client):
    response = test_client.get("/api/activity/3fa85f64-5717-4562-b3fc-2c963f66afa6")
    assert response.status_code == 404


def test_activity_action_lowercased(test_client, user_payload, activity_payload):
    test_client.post("/api/users/", json=user_payload)
    activity_payload["action"] = "LOGIN"

    response = test_client.post("/api/activity/", json=activity_payload)
    assert response.status_code == 201
    assert response.json()["Log"]["action"] == "login"


def test_activity_invalid_ip_address(test_client, user_payload):
    payload = {
        "user_id": user_payload["id"],
        "action": "login",
        "ip_address": "999.999.999.999",
    }
    response = test_client.post("/api/activity/", json=payload)
    assert response.status_code == 422
    response_json = response.json()
    detail = response_json["detail"][0]
    assert detail["type"] == "value_error"
    assert detail["loc"] == ["body", "ip_address"]
    assert detail["msg"] == "Value error, Each octet must be between 0 and 255"
    assert detail["input"] == "999.999.999.999"


def test_activity_invalid_ip_format(test_client, user_payload):
    payload = {
        "user_id": user_payload["id"],
        "action": "login",
        "ip_address": "not-an-ip",
    }
    response = test_client.post("/api/activity/", json=payload)
    assert response.status_code == 422
    response_json = response.json()
    detail = response_json["detail"][0]
    assert detail["type"] == "value_error"
    assert detail["loc"] == ["body", "ip_address"]
    assert detail["msg"] == "Value error, IP address must have 4 octets"
    assert detail["input"] == "not-an-ip"


def test_schema_model_dump_method():
    schema = ActivityLogCreateSchema(
        user_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        action="LOGIN",
        description="test",
        ip_address="10.0.0.1",
    )
    data = schema.model_dump()
    assert "user_id" in data
    assert "action" in data
    assert data["action"] == "login"

    data_exclude = schema.model_dump(exclude={"description"})
    assert "description" not in data_exclude

    data_include = schema.model_dump(include={"action", "ip_address"})
    assert set(data_include.keys()) == {"action", "ip_address"}


def test_schema_model_validate_pattern():
    class FakeOrmObj:
        id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        user_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        action = "login"
        description = "test"
        ip_address = "10.0.0.1"
        createdAt = None

    obj = FakeOrmObj()
    schema = ActivityLogResponseSchema.model_validate(obj)
    assert schema.action == "login"
    assert schema.ip_address == "10.0.0.1"


def test_schema_config_class_present():
    assert hasattr(ActivityLogCreateSchema, "Config")
    config = ActivityLogCreateSchema.Config
    assert config.from_attributes is True
    assert config.json_schema_extra is not None
    assert "example" in config.json_schema_extra
