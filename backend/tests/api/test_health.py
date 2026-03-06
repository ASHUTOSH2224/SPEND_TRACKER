def test_healthcheck_returns_envelope(client) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = response.json()
    assert payload["error"] is None
    assert payload["meta"] == {}
    assert payload["data"] == {
        "status": "ok",
        "database": "ok",
        "environment": "test",
        "version": "0.1.0",
    }


def test_openapi_exposes_health_route(client) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/health" in response.json()["paths"]
