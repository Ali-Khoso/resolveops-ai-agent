import pytest
from fastapi import HTTPException
from app.agents.settings import workflow_timeout_seconds


def test_workflow_timeout_defaults(monkeypatch):
    monkeypatch.delenv("GRAPH_TIMEOUT_SECONDS", raising=False)
    assert workflow_timeout_seconds() == 30


@pytest.mark.parametrize("value", ["0", "-1", "2", "500", "not_a_number"])
def test_workflow_timeout_rejects_unsafe_settings(monkeypatch, value):
    monkeypatch.setenv("GRAPH_TIMEOUT_SECONDS", value)
    with pytest.raises(HTTPException) as exc:
        workflow_timeout_seconds()
    assert exc.value.status_code == 503


def test_accepts_bounded_configuration(monkeypatch):
    monkeypatch.setenv("GRAPH_TIMEOUT_SECONDS", "45")
    assert workflow_timeout_seconds() == 45
