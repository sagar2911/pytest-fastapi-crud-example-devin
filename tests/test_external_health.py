import asyncio
import json
from unittest.mock import patch, MagicMock

import httpx

from app.main import app, build_proxy_client


def test_healthchecker(test_client):
    response = test_client.get("/api/healthchecker")
    assert response.status_code == 200
    assert response.json() == {"message": "The API is LIVE!!"}


def test_external_health_check(test_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.history = []

    with patch.object(
        test_client.app.state.http_client, "get", return_value=mock_response
    ):
        response = test_client.get("/api/external-health?url=https://httpbin.org/get")
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://httpbin.org/get"
        assert data["status_code"] == 200
        assert data["redirected"] is False


def test_external_health_redirect_not_followed(test_client):
    mock_response = MagicMock()
    mock_response.status_code = 302
    mock_response.history = []

    with patch.object(
        test_client.app.state.http_client, "get", return_value=mock_response
    ):
        response = test_client.get("/api/external-health/redirect-test")
        assert response.status_code == 200
        data = response.json()
        assert data["status_code"] == 302
        assert data["redirected"] is False


def test_external_health_error(test_client):
    with patch.object(
        test_client.app.state.http_client,
        "get",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        response = test_client.get("/api/external-health?url=https://badurl.example")
        assert response.status_code == 502
        assert "Failed to reach external URL" in response.json()["detail"]


def test_build_proxy_client_with_proxy():
    from app import main
    original = main.PROXY_URL
    main.PROXY_URL = "http://proxy.example.com:8080"
    try:
        client = build_proxy_client()
        assert client is not None
        client.close()
    finally:
        main.PROXY_URL = original


def test_httpx_proxy_single_url():
    client = httpx.Client(proxy="http://localhost:8080")
    assert client is not None
    client.close()


def test_async_client_with_transport():
    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/healthchecker")
            assert response.status_code == 200
            assert response.json() == {"message": "The API is LIVE!!"}

    asyncio.run(_run())


def test_async_client_with_transport_post_json():
    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/healthchecker")
            assert response.status_code == 200
            assert "LIVE" in response.json()["message"]

    asyncio.run(_run())


def test_httpx_client_default_no_redirect():
    client = httpx.Client()
    assert client.follow_redirects is False
    client.close()


def test_httpx_async_client_default_no_redirect():
    client = httpx.AsyncClient()
    assert client.follow_redirects is False


def test_httpx_json_body_format():
    request = httpx.Request("POST", "http://example.com", json={"key": "value", "num": 1})
    body = request.content.decode("utf-8")
    parsed = json.loads(body)
    assert parsed == {"key": "value", "num": 1}
    assert b":" in request.content
