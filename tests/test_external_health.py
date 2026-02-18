from unittest.mock import patch, MagicMock
import httpx


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


def test_httpx_client_initialized_with_no_redirect():
    client = httpx.Client(follow_redirects=False)
    assert client.follow_redirects is False
    client.close()


def test_httpx_client_default_no_redirect():
    client = httpx.Client()
    assert client.follow_redirects is False
    client.close()
