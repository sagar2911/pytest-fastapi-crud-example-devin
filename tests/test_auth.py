import time

import jwt

from app.auth import (
    create_access_token,
    decode_token_verified,
    decode_token_unverified,
    get_token_headers,
    JWT_SECRET,
    JWT_ALGORITHM,
)


# --- BREAKS in PyJWT 2.x: jwt.encode() returns str, not bytes ---

def test_jwt_encode_returns_bytes():
    token = jwt.encode({"sub": "user1", "exp": int(time.time()) + 3600}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    assert isinstance(token, bytes)


def test_jwt_encode_bytes_decodable():
    token = jwt.encode({"sub": "user1", "exp": int(time.time()) + 3600}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    token_str = token.decode("utf-8")
    assert "." in token_str
    parts = token_str.split(".")
    assert len(parts) == 3


# --- BREAKS in PyJWT 2.x: jwt.decode() without algorithms parameter ---

def test_jwt_decode_without_algorithms():
    token = jwt.encode({"sub": "user1", "exp": int(time.time()) + 3600}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    payload = jwt.decode(token, JWT_SECRET)
    assert payload["sub"] == "user1"


# --- BREAKS in PyJWT 2.x: verify=False parameter removed ---

def test_jwt_decode_verify_false():
    token = jwt.encode({"sub": "user1", "exp": int(time.time()) + 3600}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    payload = jwt.decode(token, JWT_SECRET, verify=False)
    assert payload["sub"] == "user1"


def test_jwt_decode_verify_false_wrong_key():
    token = jwt.encode({"sub": "user1", "exp": int(time.time()) + 3600}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    payload = jwt.decode(token, "wrong-key", verify=False)
    assert payload["sub"] == "user1"


def test_jwt_decode_verify_false_no_key():
    token = jwt.encode({"sub": "user1", "exp": int(time.time()) + 3600}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    payload = jwt.decode(token, None, verify=False)
    assert payload["sub"] == "user1"


def test_jwt_decode_expired_with_verify_false():
    token = jwt.encode({"sub": "user1", "exp": int(time.time()) - 100}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    payload = jwt.decode(token, JWT_SECRET, verify=False)
    assert payload["sub"] == "user1"


# --- BREAKS in PyJWT 2.x: exception hierarchy changed ---

def test_jwt_expired_raises_expired_signature_error():
    token = jwt.encode({"sub": "user1", "exp": int(time.time()) - 100}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    try:
        jwt.decode(token, JWT_SECRET)
        assert False, "Should have raised"
    except jwt.ExpiredSignatureError:
        pass


def test_jwt_invalid_token_raises_decode_error():
    try:
        jwt.decode("not.a.token", JWT_SECRET)
        assert False, "Should have raised"
    except jwt.DecodeError:
        pass


# --- Test auth module functions use PyJWT 1.x patterns ---

def test_create_access_token_returns_string():
    token = create_access_token("user-123")
    assert isinstance(token, str)
    assert "." in token


def test_decode_token_verified():
    token = create_access_token("user-123")
    payload = decode_token_verified(token)
    assert payload["sub"] == "user-123"


def test_decode_token_unverified():
    token = create_access_token("user-123")
    payload = decode_token_unverified(token)
    assert payload["sub"] == "user-123"


def test_get_token_headers():
    token = create_access_token("user-123")
    headers = get_token_headers(token)
    assert headers["alg"] == "HS256"
    assert headers["typ"] == "JWT"


# --- Test auth API endpoints ---

def test_create_token(test_client, user_payload):
    test_client.post("/api/users/", json=user_payload)

    response = test_client.post(
        "/api/auth/token",
        json={"user_id": user_payload["id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600


def test_create_token_user_not_found(test_client):
    response = test_client.post(
        "/api/auth/token",
        json={"user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"},
    )
    assert response.status_code == 404


def test_get_me(test_client, user_payload):
    test_client.post("/api/users/", json=user_payload)

    token_response = test_client.post(
        "/api/auth/token",
        json={"user_id": user_payload["id"]},
    )
    token = token_response.json()["access_token"]

    response = test_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_payload["id"]
    assert data["first_name"] == user_payload["first_name"]


def test_get_me_invalid_token(test_client):
    response = test_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


def test_inspect_token(test_client, user_payload):
    test_client.post("/api/users/", json=user_payload)

    token_response = test_client.post(
        "/api/auth/token",
        json={"user_id": user_payload["id"]},
    )
    token = token_response.json()["access_token"]

    response = test_client.get(
        "/api/auth/inspect",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["headers"]["alg"] == "HS256"
    assert data["payload"]["sub"] == user_payload["id"]
    assert data["signature_valid"] is True
