"""Testes unitários para o filtro de PII do Sentry (LGPD)."""

from app.core.sentry_client import _filter_pii

REDACTED = "<redacted>"


def _event(**extra: object) -> dict:
    return {"event_id": "abc", **extra}


def test_redacts_sensitive_frame_vars():
    event = _event(
        exception={
            "values": [{"stacktrace": {"frames": [{"vars": {"password": "x", "user_id": "42"}}]}}]
        }
    )
    out = _filter_pii(event, {})
    frame_vars = out["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"]
    assert frame_vars["password"] == REDACTED
    assert frame_vars["user_id"] == "42"


def test_redacts_request_body_by_key():
    event = _event(
        request={
            "url": "https://api.example.test/v1/auth/register",
            "data": {
                "email": "maria@example.com",
                "cpf": "123.456.789-09",
                "password": "Senha123!",
                "full_name_len": 5,
            },
        }
    )
    out = _filter_pii(event, {})
    data = out["request"]["data"]
    assert data["email"] == REDACTED
    assert data["cpf"] == REDACTED
    assert data["password"] == REDACTED
    assert data["full_name_len"] == 5


def test_redacts_nested_request_data():
    event = _event(request={"data": {"profile": {"phone": "11999998888", "city": "SP"}}})
    out = _filter_pii(event, {})
    assert out["request"]["data"]["profile"]["phone"] == REDACTED
    assert out["request"]["data"]["profile"]["city"] == "SP"


def test_redacts_request_headers_and_cookies():
    event = _event(
        request={
            "headers": {"Authorization": "Bearer abc", "X-Api-Key": "k", "Accept": "json"},
            "cookies": {"access_token": "abc"},
        }
    )
    out = _filter_pii(event, {})
    assert out["request"]["headers"]["Authorization"] == REDACTED
    assert out["request"]["headers"]["X-Api-Key"] == REDACTED
    assert out["request"]["headers"]["Accept"] == "json"
    assert out["request"]["cookies"] == REDACTED


def test_redacts_email_and_cpf_inside_free_text():
    event = _event(
        request={
            "query_string": "email=maria%40example.com&cpf=12345678909&page=2",
            "data": "raw body maria@example.com 123.456.789-09",
        },
        breadcrumbs={"values": [{"message": "login falhou para joao@example.com"}]},
    )
    out = _filter_pii(event, {})
    assert "maria" not in out["request"]["query_string"]
    assert "12345678909" not in out["request"]["query_string"]
    assert "page=2" in out["request"]["query_string"]
    assert "maria@example.com" not in out["request"]["data"]
    assert "123.456.789-09" not in out["request"]["data"]
    assert "joao@example.com" not in out["breadcrumbs"]["values"][0]["message"]


def test_user_keeps_only_id():
    event = _event(user={"id": "u-1", "email": "a@b.com", "ip_address": "1.2.3.4"})
    out = _filter_pii(event, {})
    assert out["user"] == {"id": "u-1"}


def test_does_not_overredact_words_containing_short_keys():
    """'rg' e 'key' não podem apagar campos como 'organization' ou 'monkey'."""
    event = _event(request={"data": {"organization": "ACME", "monkey": "x", "rg": "12.345"}})
    out = _filter_pii(event, {})
    data = out["request"]["data"]
    assert data["organization"] == "ACME"
    assert data["monkey"] == "x"
    assert data["rg"] == REDACTED


def test_event_without_pii_sections_is_untouched():
    event = _event(message="boom")
    assert _filter_pii(event, {}) == {"event_id": "abc", "message": "boom"}
